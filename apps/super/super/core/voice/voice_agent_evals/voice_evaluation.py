"""
Voice Call Evaluation System
Independent evaluation system inspired by evals-course-voice
Stores conversation turns, audio, and metrics in MongoDB
Does NOT depend on post_call.py
"""

import os
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from difflib import SequenceMatcher

# MongoDB imports - Initialize connection first
# Import OID patch first to fix Pydantic v2 compatibility
from super_services.libs.core.model import *  # This applies the OID patch
from super_services.db.services import *  # This initializes MongoDB connection
from super_services.db.services.models.voice_evaluation import (
    CallSessionModel, CallSessionBaseModel,
    ConversationTurnModel, ConversationTurnBaseModel,
    CallEvaluationResultModel, CallEvaluationResultBaseModel,
    CallQualityMetricsModel, CallQualityMetricsBaseModel,
    QuestionNotFoundModel, QuestionNotFoundBaseModel
)
from bson import ObjectId
from mongomantic.core.errors import DoesNotExistError

# Optional: OpenTelemetry for tracing (like 002-bot-otel.py)
IS_TRACING_ENABLED = bool(os.getenv("ENABLE_TRACING"))

if IS_TRACING_ENABLED:
    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry import trace

        otlp_exporter = OTLPSpanExporter()
        provider = TracerProvider()
        processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        print("✅ OpenTelemetry tracing initialized")
    except Exception as e:
        print(f"⚠️ Tracing setup failed: {e}")
        IS_TRACING_ENABLED = False


class VoiceCallEvaluator:
    """
    Independent Voice Call Evaluation System
    Evaluates voice calls against ground truth QA pairs
    Stores conversation turns and audio in MongoDB
    """

    def __init__(
            self,
            agent_id: str = None,
            recordings_dir: str = None,
    ):
        """
        Initialize VoiceCallEvaluator.

        Args:
            agent_id: Agent handle to load QA pairs from MongoDB
            recordings_dir: Directory for audio recordings (optional)
        """
        self.agent_id = agent_id

        # Use absolute paths for better reliability
        base_dir = Path(__file__).parent
        self.recordings_dir = Path(recordings_dir) if recordings_dir else base_dir / "db-and-recordings"
        self.recordings_dir.mkdir(parents=True, exist_ok=True)

        # Load QA pairs from MongoDB for this agent
        self.ground_truth = self._load_qa_pairs_from_db()
        print(f"✅ VoiceCallEvaluator initialized for agent: {agent_id}")

    def _load_qa_pairs_from_db(self) -> List[Dict[str, Any]]:
        """
        Load QA pairs from MongoDB for the specified agent.

        Returns:
            List of QA pairs with questions, answers, and keywords
        """
        if not self.agent_id:
            print("⚠️ No agent_id provided, cannot load QA pairs from MongoDB")
            return []

        try:
            from super_services.evals.eval_generator import get_all_qa_pairs_for_agent
            qa_pairs = get_all_qa_pairs_for_agent(self.agent_id)

            if not qa_pairs:
                print(f"⚠️ No QA pairs found in MongoDB for agent: {self.agent_id}")
                return []

            print(f"✅ Loaded {len(qa_pairs)} QA pairs from MongoDB for agent: {self.agent_id}")

            # Preprocess all QA pairs
            for qa in qa_pairs:
                # Ensure required fields exist
                if 'question' not in qa or 'answer' not in qa:
                    print(f"⚠️ Skipping invalid QA pair - missing required fields: {qa}")
                    continue

                # Ensure keywords exist and are lowercase
                if 'keywords' not in qa or not qa['keywords']:
                    # If no keywords, generate some from the question
                    words = [word.lower() for word in qa['question'].split() if len(word) > 2]
                    qa['keywords'] = list(set(words))  # Remove duplicates
                else:
                    # Ensure all keywords are lowercase
                    qa['keywords'] = [kw.lower() for kw in qa['keywords']]

                # Add question words as additional keywords if they're not already there
                question_words = [word.lower() for word in qa['question'].split()
                               if len(word) > 2 and word.lower() not in qa['keywords']]
                qa['keywords'].extend(question_words)

                # Add n-grams for better matching (bi-grams and tri-grams)
                words = qa['question'].lower().split()
                for n in [2, 3]:  # bi-grams and tri-grams
                    ngrams = [' '.join(words[i:i+n]) for i in range(len(words)-n+1)]
                    qa['keywords'].extend(ngrams)

                # Remove duplicates and ensure unique keywords
                qa['keywords'] = list(set(qa['keywords']))

            print(f"✅ Total QA pairs processed: {len(qa_pairs)}")
            return qa_pairs

        except Exception as e:
            print(f"❌ Error loading QA pairs from MongoDB: {e}")
            import traceback
            traceback.print_exc()
            return []

    def extract_audio_chunk(self, wav_file_path: str, start_time: float, end_time: float) -> Optional[bytes]:
        """
        Extract a chunk of audio from WAV file based on timestamps (like o3-bot-sqlite.py)

        Args:
            wav_file_path: Path to the WAV file
            start_time: Start time in seconds
            end_time: End time in seconds

        Returns:
            bytes: WAV audio chunk as bytes, or None if extraction fails
        """
        try:
            import wave
            import io

            with wave.open(wav_file_path, 'rb') as wav_file:
                framerate = wav_file.getframerate()
                n_channels = wav_file.getnchannels()
                sampwidth = wav_file.getsampwidth()

                # Calculate frame positions
                start_frame = int(start_time * framerate)
                end_frame = int(end_time * framerate)

                # Set position and read frames
                wav_file.setpos(start_frame)
                frames = wav_file.readframes(end_frame - start_frame)

                # Create a new WAV in memory
                output = io.BytesIO()
                with wave.open(output, 'wb') as out_wav:
                    out_wav.setnchannels(n_channels)
                    out_wav.setsampwidth(sampwidth)
                    out_wav.setframerate(framerate)
                    out_wav.writeframes(frames)

                return output.getvalue()

        except Exception as e:
            print(f"⚠️ Error extracting audio chunk: {e}")
            return None

    def save_conversation_turn(
            self,
            session_id: str,
            turn_number: int,
            turn_start_time: float,
            turn_end_time: float,
            user_speech_text: str,
            llm_response_text: str,
            voice_to_voice_response_time: float,
            interrupted: bool = False,
            wav_audio: bytes = None,
            space_token: Optional[str] = None
    ):
        """Save individual conversation turn with optional audio to MongoDB"""
        try:
            # Check if turn already exists using get()
            existing = None
            try:
                existing = ConversationTurnModel.get(
                    session_id=session_id,
                    turn_number=turn_number
                )
            except DoesNotExistError:
                existing = None  # Document doesn't exist, will create new

            turn_data = {
                "space_token": space_token,
                "session_id": session_id,
                "turn_number": turn_number,
                "turn_start_time": turn_start_time,
                "turn_end_time": turn_end_time,
                "user_speech_text": user_speech_text,
                "llm_response_text": llm_response_text,
                "voice_to_voice_response_time": voice_to_voice_response_time,
                "interrupted": interrupted,
                "wav_audio": wav_audio
            }

            if existing:
                # Update existing record using pymongo collection directly
                ConversationTurnModel._get_collection().update_one(
                    {"session_id": session_id, "turn_number": turn_number},
                    {"$set": turn_data}
                )
            else:
                # Insert new record - add id for MongoDB
                turn_data["id"] = ObjectId()
                turn = ConversationTurnBaseModel(**turn_data)
                ConversationTurnModel.save(turn)

        except Exception as e:
            print(f"⚠️ Error saving conversation turn: {e}")
            import traceback
            traceback.print_exc()

    def save_call_session(
            self,
            session_id: str,
            agent_id: str,
            call_start_time,
            call_end_time,
            transcript: List[Dict],
            audio_file_path: Optional[str] = None,
            space_token: Optional[str] = None
    ):
        """Save call session information to MongoDB

        Args:
            session_id: Unique session identifier
            agent_id: Agent identifier
            call_start_time: Start time as Unix timestamp (float) or ISO format string
            call_end_time: End time as Unix timestamp (float) or ISO format string
            transcript: List of conversation messages
            audio_file_path: Path to the audio file (optional)
            space_token: Space token for tracking which space this call belongs to (optional)
        """
        try:
            # Convert string timestamps to Unix timestamps if needed
            if isinstance(call_start_time, str):
                try:
                    dt = datetime.fromisoformat(call_start_time.replace('Z', '+00:00'))
                    call_start_time = dt.timestamp()
                except (ValueError, AttributeError) as e:
                    print(f"⚠️ Error parsing start time '{call_start_time}': {e}")
                    call_start_time = time.time() - 60  # Default to 1 minute ago

            if isinstance(call_end_time, str):
                try:
                    dt = datetime.fromisoformat(call_end_time.replace('Z', '+00:00'))
                    call_end_time = dt.timestamp()
                except (ValueError, AttributeError) as e:
                    print(f"⚠️ Error parsing end time '{call_end_time}': {e}")
                    call_end_time = time.time()

            total_duration = call_end_time - call_start_time
            transcript_json = json.dumps(transcript)

            # Check if session already exists using get()
            existing = None
            try:
                existing = CallSessionModel.get(session_id=session_id)
            except DoesNotExistError:
                existing = None  # Document doesn't exist, will create new

            session_data = {
                "space_token": space_token,
                "session_id": session_id,
                "agent_id": agent_id,
                "call_start_time": call_start_time,
                "call_end_time": call_end_time,
                "duration": total_duration,
                "audio_file_path": audio_file_path,
                "transcript": transcript_json
            }

            if existing:
                # Update existing record using pymongo collection directly
                CallSessionModel._get_collection().update_one(
                    {"session_id": session_id},
                    {"$set": session_data}
                )
            else:
                # Insert new record - add id for MongoDB
                session_data["id"] = ObjectId()
                session = CallSessionBaseModel(**session_data)
                CallSessionModel.save(session)

            print(f"✅ Successfully saved call session {session_id}")
            return True

        except Exception as e:
            print(f"❌ Error saving call session {session_id}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def save_audio_recording(
            self,
            session_id: str,
            audio_data: bytes,
            file_format: str = "wav"
    ) -> str:
        """Save audio recording to disk (like 003-bot)"""
        audio_file = self.recordings_dir / f"conversation-{session_id}.{file_format}"

        with open(audio_file, "wb") as f:
            f.write(audio_data)

        print(f"🔊 Audio saved: {audio_file}")
        return str(audio_file)

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts using a combination of techniques.
        Returns a score between 0.0 (completely different) and 1.0 (identical).
        """
        if not text1 or not text2:
            return 0.0

        # Convert to lowercase for case-insensitive comparison
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()

        # If either text is empty after normalization, return 0
        if not text1 or not text2:
            return 0.0

        # 1. Sequence matcher (character-based similarity)
        seq_match = SequenceMatcher(None, text1, text2).ratio()

        # 2. Jaccard similarity (word-based similarity)
        words1 = set(text1.split())
        words2 = set(text2.split())
        if not words1 and not words2:
            jaccard = 1.0
        else:
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            jaccard = intersection / union if union > 0 else 0.0

        # 3. Check for containment (is one text contained within the other?)
        containment = 1.0 if (text1 in text2 or text2 in text1) else 0.5

        # Combine the scores with weights
        # Give more weight to sequence match and containment
        combined_score = (seq_match * 0.5) + (jaccard * 0.3) + (containment * 0.2)

        # Ensure the score is within [0, 1]
        return max(0.0, min(1.0, combined_score))

    def _calculate_relevancy(self, reply: str, expected: str) -> float:
        """
        Calculate how relevant the reply is to the expected answer.
        Considers keyword matching, semantic similarity, and contextual relevance.
        Returns a score between 0.0 (irrelevant) and 1.0 (highly relevant).
        """
        if not reply or not expected:
            return 0.0

        # Convert to lowercase for case-insensitive comparison
        reply = reply.lower().strip()
        expected = expected.lower().strip()

        # If either text is empty after normalization, return 0
        if not reply or not expected:
            return 0.0

        # 1. Keyword matching with stemming and lemmatization
        try:
            from nltk.stem import WordNetLemmatizer
            from nltk.tokenize import word_tokenize

            # Initialize lemmatizer
            lemmatizer = WordNetLemmatizer()

            # Tokenize and lemmatize words, removing stopwords and short words
            stop_words = set(['the', 'a', 'an', 'in', 'on', 'at', 'and', 'or', 'but', 'is', 'are', 'was', 'were'])

            def process_text(text):
                words = word_tokenize(text.lower())
                return [lemmatizer.lemmatize(word) for word in words
                       if word.isalnum() and word not in stop_words and len(word) > 2]

            expected_keywords = set(process_text(expected))
            reply_keywords = set(process_text(reply))

            # Calculate keyword coverage
            if not expected_keywords:
                keyword_coverage = 0.0
            else:
                matched_keywords = expected_keywords.intersection(reply_keywords)
                keyword_coverage = len(matched_keywords) / len(expected_keywords)
        except ImportError:
            # Fallback to simple word matching if NLTK is not available
            expected_keywords = set(word.lower() for word in expected.split() if len(word) > 3)
            reply_keywords = set(word.lower() for word in reply.split())
            if not expected_keywords:
                keyword_coverage = 0.0
            else:
                keyword_coverage = len(expected_keywords.intersection(reply_keywords)) / len(expected_keywords)

        # 2. Semantic similarity using sequence matcher
        similarity = self._calculate_similarity(reply, expected)

        # 3. Check for question-answer relationship
        # If the reply contains the expected answer or vice versa, it's highly relevant
        if expected in reply or reply in expected:
            semantic_relation = 1.0
        else:
            semantic_relation = 0.5

        # 4. Length ratio (penalize very short or very long answers)
        len_ratio = min(len(reply.split()) / max(1, len(expected.split())), 2.0)  # Cap at 2.0
        if len_ratio > 1.0:
            len_score = 1.0 / len_ratio  # Penalize answers that are too long
        else:
            len_score = len_ratio  # Reward answers that are not too short

        # Combine the scores with weights
        combined_score = (
            (keyword_coverage * 0.4) +
            (similarity * 0.3) +
            (semantic_relation * 0.2) +
            (len_score * 0.1)
        )

        # Ensure the score is within [0, 1]
        return max(0.0, min(1.0, combined_score))

    def _calculate_completeness(self, reply: str, expected: str) -> float:
        """
        Calculate how complete the reply is compared to the expected answer.
        Considers coverage of key points, concepts, and details.
        Returns a score between 0.0 (incomplete) and 1.0 (complete).
        """
        if not reply or not expected:
            return 0.0

        # Convert to lowercase for case-insensitive comparison
        reply = reply.lower().strip()
        expected = expected.lower().strip()

        # If either text is empty after normalization, return 0
        if not reply or not expected:
            return 0.0

        # 1. Sentence-level coverage
        # Split into sentences, handling various sentence terminators and whitespace
        import re
        expected_sentences = [s.strip() for s in re.split(r'[.!?]+', expected) if s.strip()]

        # If no sentences found, try splitting by newlines or other delimiters
        if not expected_sentences:
            expected_sentences = [s.strip() for s in re.split(r'[\n\r]+', expected) if s.strip()]

        # If still no sentences, use the whole text as one sentence
        if not expected_sentences:
            expected_sentences = [expected]

        # Calculate how many expected sentences are covered in the reply
        covered_sentences = 0
        for sent in expected_sentences:
            # Check if the sentence is present in the reply
            # Use a more lenient check that allows for minor variations
            if len(sent.split()) <= 3:  # Very short sentences might be false positives
                if sent in reply:
                    covered_sentences += 1
            else:
                # For longer sentences, use similarity to account for minor differences
                words = sent.split()
                # Check if most words from the sentence appear in the reply
                matched_words = sum(1 for word in words if word in reply)
                if matched_words / len(words) >= 0.7:  # At least 70% of words match
                    covered_sentences += 1

        sentence_coverage = covered_sentences / len(expected_sentences) if expected_sentences else 0.0

        # 2. Keyword coverage (similar to relevancy but focused on completeness)
        try:
            from nltk.tokenize import word_tokenize
            from nltk.corpus import stopwords
            from nltk import pos_tag

            # Get content words (nouns, verbs, adjectives, adverbs) from expected
            words = word_tokenize(expected)
            tagged = pos_tag(words)
            content_words = [word.lower() for word, pos in tagged
                           if pos.startswith(('NN', 'VB', 'JJ', 'RB'))
                           and word.lower() not in stopwords.words('english')
                           and len(word) > 2]
        except (ImportError, LookupError):
            # Fallback to simple word filtering if NLTK is not available
            content_words = [word.lower() for word in expected.split()
                           if len(word) > 3]

        # Calculate keyword coverage
        if content_words:
            matched_keywords = sum(1 for word in set(content_words) if word in reply)
            keyword_coverage = matched_keywords / len(set(content_words)) if content_words else 0.0
        else:
            keyword_coverage = 0.0

        # 3. Length ratio (penalize very short answers)
        len_ratio = min(len(reply.split()) / max(1, len(expected.split())), 1.5)  # Cap at 1.5

        # 4. Combine scores with weights
        combined_score = (
            (sentence_coverage * 0.5) +
            (keyword_coverage * 0.3) +
            (len_ratio * 0.2)
        )

        # Ensure the score is within [0, 1]
        return max(0.0, min(1.0, combined_score))

    def _calculate_accuracy(self, reply: str, expected: str) -> float:
        """
        Calculate the overall accuracy of the reply compared to the expected answer.
        This is a composite metric that combines similarity, relevancy, and completeness.
        Returns a score between 0.0 (inaccurate) and 1.0 (highly accurate).
        """
        if not reply or not expected:
            return 0.0

        # Calculate individual metrics
        similarity = self._calculate_similarity(reply, expected)
        relevancy = self._calculate_relevancy(reply, expected)
        completeness = self._calculate_completeness(reply, expected)

        # Calculate a weighted average
        # Give more weight to relevancy and completeness than raw similarity
        accuracy = (
            (similarity * 0.2) +
            (relevancy * 0.4) +
            (completeness * 0.4)
        )

        # Apply a length penalty for very short or very long answers
        reply_len = len(reply.split())
        expected_len = len(expected.split())

        if expected_len > 0:
            length_ratio = reply_len / expected_len
            if length_ratio < 0.5:  # Very short answer
                accuracy *= 0.7  # Penalize by 30%
            elif length_ratio > 2.0:  # Very long answer
                accuracy *= 0.9  # Slight penalty for verbosity

        # Ensure the score is within [0, 1]
        return max(0.0, min(1.0, accuracy))

    async def evaluate_call_quality(self, session_id: str, transcript: List[Dict], turn_metrics: Dict = None, space_token: Optional[str] = None) -> List[Dict]:
        """
        Evaluate call quality by comparing user-agent message pairs with ground truth

        Args:
            session_id: Unique session identifier
            transcript: List of messages with 'role' and 'content' keys
            turn_metrics: Optional dictionary containing per-turn cost and latency metrics from observer
            space_token: Optional space token for tracking which space this call belongs to

        Returns:
            List of evaluation results for each message pair
        """
        print(f"\n🔍 [DEBUG] Starting evaluation for session: {session_id}")
        print(f"🔍 [DEBUG] Transcript length: {len(transcript)} messages")

        # Convert transcript to message pairs with turn numbers
        message_pairs = []
        turn_number = 0

        # Process messages with a while loop for better control
        i = 0
        while i < len(transcript):
            try:
                msg = transcript[i]
                if not isinstance(msg, dict):
                    print(f"⚠️ Invalid message format at index {i}, expected dict, got {type(msg).__name__}")
                    i += 1
                    continue

                role = msg.get('role')
                if not role:
                    print(f"⚠️ Missing 'role' in message at index {i}")
                    i += 1
                    continue

                content = str(msg.get('content', '')).strip()

                # Convert timestamp to float if it's a string
                timestamp = msg.get('timestamp')
                if isinstance(timestamp, str):
                    try:
                        # Try to parse ISO format timestamp
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        timestamp = dt.timestamp()
                    except (ValueError, AttributeError):
                        # Fallback to current time if parsing fails
                        timestamp = time.time()

                turn_number += 1
                current_time = time.time()

                print(f"🔍 [DEBUG] Turn {turn_number} - {role.capitalize()}:")
                print(f"  {content[:200]}{'...' if len(content) > 200 else ''}")

                # Save every message to the database, regardless of role or content
                try:
                    if role.lower() == 'user':
                        # For user messages, check if there's an assistant response following
                        if (i + 1 < len(transcript) and
                            isinstance(transcript[i+1], dict) and
                            transcript[i+1].get('role', '').lower() == 'assistant' and
                            'content' in transcript[i+1]):

                            next_msg = transcript[i+1]
                            agent_content = str(next_msg.get('content', '')).strip()
                            agent_timestamp = next_msg.get('timestamp')

                            # Convert agent timestamp if needed
                            if isinstance(agent_timestamp, str):
                                try:
                                    dt = datetime.fromisoformat(agent_timestamp.replace('Z', '+00:00'))
                                    agent_timestamp = dt.timestamp()
                                except (ValueError, AttributeError):
                                    agent_timestamp = current_time + 1.0  # Add 1 second if parsing fails

                            # Calculate response time
                            response_time = (agent_timestamp - timestamp) if (agent_timestamp and timestamp) else 0.0

                            # Save the conversation turn to database
                            self.save_conversation_turn(
                                session_id=session_id,
                                turn_number=turn_number,
                                turn_start_time=float(timestamp) if timestamp else current_time,
                                turn_end_time=float(agent_timestamp) if agent_timestamp else current_time + 1.0,
                                user_speech_text=content,
                                llm_response_text=agent_content,
                                voice_to_voice_response_time=response_time,
                                interrupted=False
                            )
                            print(f"   💾 Saved user-assistant turn {turn_number} to database")

                            if agent_content:  # Only add if there's actual content
                                message_pairs.append({
                                    'turn': turn_number,
                                    'user': content,
                                    'agent': agent_content,
                                    'user_timestamp': timestamp,
                                    'agent_timestamp': agent_timestamp,
                                    'evaluation_type': 'user_agent_pair'
                                })
                                print(f"   ✅ Paired with assistant response: {agent_content[:100]}...")
                                i += 2  # Skip the assistant message in the next iteration
                                continue  # Skip the rest of the loop for this iteration

                        # If we get here, it's a user message without a following assistant message
                        self.save_conversation_turn(
                            session_id=session_id,
                            turn_number=turn_number,
                            turn_start_time=float(timestamp) if timestamp else current_time,
                            turn_end_time=float(timestamp) + 1.0 if timestamp else current_time + 1.0,
                            user_speech_text=content,
                            llm_response_text='',
                            voice_to_voice_response_time=0.0,
                            interrupted=True
                        )
                        print(f"   💾 Saved standalone user message (turn {turn_number}) to database")

                        message_pairs.append({
                            'turn': turn_number,
                            'content': content,
                            'role': role,
                            'timestamp': timestamp,
                            'evaluation_type': 'standalone_user'
                        })

                    elif role.lower() == 'assistant':
                        # For assistant messages without a preceding user message
                        self.save_conversation_turn(
                            session_id=session_id,
                            turn_number=turn_number,
                            turn_start_time=float(timestamp) - 1.0 if timestamp else current_time - 1.0,
                            turn_end_time=float(timestamp) if timestamp else current_time,
                            user_speech_text='',
                            llm_response_text=content,
                            voice_to_voice_response_time=0.0,
                            interrupted=True
                        )
                        print(f"   💾 Saved standalone assistant message (turn {turn_number}) to database")

                        message_pairs.append({
                            'turn': turn_number,
                            'content': content,
                            'role': role,
                            'timestamp': timestamp,
                            'evaluation_type': 'standalone_assistant'
                        })

                    else:
                        # For any other role (system, etc.)
                        self.save_conversation_turn(
                            session_id=session_id,
                            turn_number=turn_number,
                            turn_start_time=float(timestamp) if timestamp else current_time,
                            turn_end_time=float(timestamp) + 1.0 if timestamp else current_time + 1.0,
                            user_speech_text='',
                            llm_response_text=content,
                            voice_to_voice_response_time=0.0,
                            interrupted=True
                        )
                        print(f"   💾 Saved {role} message (turn {turn_number}) to database")

                        message_pairs.append({
                            'turn': turn_number,
                            'content': content,
                            'role': role,
                            'timestamp': timestamp,
                            'evaluation_type': f'standalone_{role}'
                        })

                except Exception as e:
                    print(f"   ⚠️ Error saving message to database: {str(e)}")

                i += 1  # Move to the next message

            except Exception as e:
                print(f"⚠️ Error processing message at index {i}: {str(e)}")
                if i < len(transcript):
                    print(f"   Message data: {transcript[i]}")
                i += 1  # Make sure to always increment to avoid infinite loop

        print(f"\n🔍 Evaluating call quality for session: {session_id}")
        print("=" * 80)
        print(f"📝 Found {len([m for m in message_pairs if m['evaluation_type'] == 'user_agent_pair'])} user-agent message pairs")
        print(f"📊 Total turns processed: {len(message_pairs)}")
        print(f"🔍 [DEBUG] Ground truth QA pairs: {len(self.ground_truth)}")
        print()

        if not message_pairs:
            error_msg = "⚠️ No message pairs provided for evaluation"
            print(error_msg)
            print("🔍 [DEBUG] Transcript content:")
            for i, msg in enumerate(transcript):
                print(f"  {i}. {msg['role']}: {msg['content'][:100]}" +
                      ("..." if len(msg['content']) > 100 else ""))
            return []

        evaluations = []

        try:
            for pair in message_pairs:
                turn_number = pair['turn']

                # Handle different message types
                if pair['evaluation_type'] == 'user_agent_pair':
                    if 'user' not in pair or 'agent' not in pair:
                        print(f"  ⚠️ Missing required fields in message pair: {pair}")
                        continue
                    user_question = pair['user']
                    agent_reply = pair['agent']
                    eval_type = 'user_agent_pair'
                else:
                    # Handle standalone messages
                    if pair.get('role') == 'assistant':
                        user_question = ""
                        agent_reply = pair['content']
                        eval_type = 'standalone_assistant'
                    else:
                        user_question = pair['content']
                        agent_reply = ""
                        eval_type = 'standalone_user'

                # Skip if both user_question and agent_reply are empty
                if not user_question and not agent_reply:
                    print(f"  ⚠️ Empty message in turn {turn_number}")
                    continue

                print(f"\n🔄 Processing Turn {turn_number} ({eval_type}):")
                if user_question:
                    print(f"   👤 User: {user_question}")
                if agent_reply:
                    print(f"   🤖 Agent: {agent_reply[:100]}{'...' if len(agent_reply) > 100 else ''}")

                # Initialize default values
                matched_qa = None
                best_score = 0
                matched_keywords = []

                # For user messages or user-agent pairs, try to find matching QA pairs
                if user_question:
                    user_question_lower = user_question.lower()

                    # First pass: Look for exact keyword matches
                    for qa in self.ground_truth:
                        keywords = qa.get('keywords', [])
                        if not keywords:
                            continue

                        # Calculate keyword match score
                        score = sum(1 for k in keywords if k.lower() in user_question_lower)

                        # If we have at least 2 keyword matches, consider it a potential match
                        if score >= 2 and score > best_score:
                            best_score = score
                            matched_qa = qa

                    # If no good match found, try fuzzy matching on the question
                    if best_score < 2 and user_question_lower:
                        from difflib import get_close_matches

                        # Get all questions from QA pairs
                        all_questions = [qa['question'].lower() for qa in self.ground_truth]

                        # Find closest matching question
                        matches = get_close_matches(user_question_lower, all_questions, n=1, cutoff=0.6)

                        if matches:
                            # Find the QA pair with the matching question
                            matched_qa = next((qa for qa in self.ground_truth
                                             if qa['question'].lower() == matches[0]), None)
                            if matched_qa:
                                best_score = 2  # Set a decent score for fuzzy matches

                # For standalone assistant messages, try to find matching answers
                elif agent_reply and not user_question:
                    agent_reply_lower = agent_reply.lower()

                    # First try to match with answer content
                    for qa in self.ground_truth:
                        if 'answer' in qa and qa['answer'].lower() in agent_reply_lower:
                            matched_qa = qa
                            best_score = 3  # High score for direct answer match
                            break

                    # If no direct answer match, try to match with questions
                    if best_score == 0:
                        for qa in self.ground_truth:
                            # Check if any keywords from the QA pair are in the agent's reply
                            keywords = qa.get('keywords', [])
                            score = sum(1 for k in keywords if k.lower() in agent_reply_lower)

                            if score >= 2 and score > best_score:
                                best_score = score
                                matched_qa = qa

                # Initialize default values
                similarity = 0.0
                relevancy = 0.0
                completeness = 0.0
                accuracy = 0.0

                if matched_qa:
                    eval_question = matched_qa.get('question', 'No question text available')
                    expected_output = matched_qa.get('answer', 'No expected answer available')
                    matched_keywords = matched_qa.get('keywords', [])

                    # Calculate metrics based on the type of message
                    if user_question and agent_reply:  # User-agent pair
                        similarity = self._calculate_similarity(agent_reply, expected_output)
                        relevancy = self._calculate_relevancy(agent_reply, expected_output)
                        completeness = self._calculate_completeness(agent_reply, expected_output)
                        accuracy = self._calculate_accuracy(agent_reply, expected_output)
                    elif agent_reply:  # Standalone assistant message
                        # For standalone assistant messages, check if the expected answer is in the response
                        if 'answer' in matched_qa and matched_qa['answer'].lower() in agent_reply.lower():
                            similarity = 1.0
                            relevancy = 1.0
                            completeness = 1.0
                            accuracy = 1.0
                else:
                    eval_question = "No matching question found"
                    expected_output = "No expected output available"
                    matched_keywords = []

                    # For standalone assistant messages without a match, we can't evaluate
                    if agent_reply and not user_question:
                        similarity = 0.0
                        relevancy = 0.0
                        completeness = 0.0
                        accuracy = 0.0
                    # For user messages without a match, we can't evaluate the response
                    elif user_question:
                        similarity = 0.0
                        relevancy = 0.0
                        completeness = 0.0
                        accuracy = 0.0

                # Log the match if we found one
                if matched_qa and best_score > 0:
                    print(f"   ✅ Matched QA: {matched_qa.get('question', 'No question')[:80]}... (score: {best_score})")

                # Calculate overall quality as average of all metrics
                overall_quality = (similarity + relevancy + completeness + accuracy) / 4.0

                # Determine if question was found (matched with QA pairs)
                # Only true when user_question exists and matches with eval_question
                question_found = matched_qa is not None and best_score > 0 and bool(user_question and user_question.strip())

                # Prepare the evaluation result in the desired format
                evaluation = {
                    'turn_number': turn_number,
                    'user_question': user_question if user_question else "",
                    'eval_question': eval_question,
                    'question_found': question_found,
                    'agent_reply': agent_reply if agent_reply else "",
                    'expected_output': expected_output,
                    'metrics': {
                        'similarity': similarity,
                        'relevancy': relevancy,
                        'completeness': completeness,
                        'accuracy': accuracy,
                        'overall_quality': overall_quality
                    },
                    'matched_keywords': matched_keywords
                }

                # Save the evaluation result to MongoDB
                try:
                    eval_data = {
                        "id": ObjectId(),  # Add id for MongoDB
                        "space_token": space_token,
                        "session_id": session_id,
                        "turn_number": turn_number,
                        "user_question": user_question,
                        "eval_question": eval_question,
                        "question_found": question_found,
                        "agent_reply": agent_reply,
                        "expected_output": expected_output,
                        "similarity": similarity,
                        "relevancy": relevancy,
                        "completeness": completeness,
                        "accuracy": accuracy,
                        "overall_quality": overall_quality,
                        "matched_keywords": json.dumps(matched_keywords) if matched_keywords else ""
                    }

                    # Add cost and latency metrics from observer if available
                    if turn_metrics:
                        # Try multiple turn key formats to handle potential off-by-one issues
                        turn_key = f"turn_{turn_number}"
                        turn_data = None

                        # First try exact match
                        if turn_key in turn_metrics:
                            turn_data = turn_metrics[turn_key]
                            print(f"   🔍 Found turn metrics for {turn_key}")
                        else:
                            # Try off-by-one (turn_number - 1) in case of mismatch
                            alt_key = f"turn_{turn_number - 1}" if turn_number > 0 else None
                            if alt_key and alt_key in turn_metrics:
                                turn_data = turn_metrics[alt_key]
                                print(f"   🔍 Found turn metrics using alternate key {alt_key}")
                            else:
                                print(f"   ⚠️ No turn metrics found for {turn_key} or {alt_key}. Available keys: {list(turn_metrics.keys())}")

                        if turn_data:
                            # Add costs
                            eval_data["llm_cost"] = turn_data.get("costs", {}).get("llm_cost", 0.0)
                            eval_data["stt_cost"] = turn_data.get("costs", {}).get("stt_cost", 0.0)
                            eval_data["tts_cost"] = turn_data.get("costs", {}).get("tts_cost", 0.0)

                            # Add usage
                            eval_data["llm_prompt_tokens"] = turn_data.get("usage", {}).get("llm_prompt_tokens", 0)
                            eval_data["llm_completion_tokens"] = turn_data.get("usage", {}).get("llm_completion_tokens", 0)
                            eval_data["stt_duration"] = turn_data.get("usage", {}).get("stt_duration", 0.0)
                            eval_data["tts_characters"] = turn_data.get("usage", {}).get("tts_characters", 0)

                            # Add latencies (in milliseconds)
                            eval_data["llm_latency"] = turn_data.get("latencies", {}).get("llm_latency", 0.0)
                            eval_data["stt_latency"] = turn_data.get("latencies", {}).get("stt_latency", 0.0)
                            eval_data["tts_latency"] = turn_data.get("latencies", {}).get("tts_latency", 0.0)

                            # Add TTFB (in seconds)
                            eval_data["llm_ttfb"] = turn_data.get("ttfb", {}).get("llm_ttfb", 0.0)
                            eval_data["stt_ttfb"] = turn_data.get("ttfb", {}).get("stt_ttfb", 0.0)
                            eval_data["tts_ttfb"] = turn_data.get("ttfb", {}).get("tts_ttfb", 0.0)

                            print(f"   📊 Turn {turn_number} costs: LLM={eval_data['llm_cost']:.4f}, STT={eval_data['stt_cost']:.4f}, TTS={eval_data['tts_cost']:.4f}")
                            print(f"   📊 Turn {turn_number} latencies: LLM={eval_data['llm_latency']:.2f}ms, STT={eval_data['stt_latency']:.2f}ms, TTS={eval_data['tts_latency']:.2f}ms")
                            print(f"   ⏱️ Turn {turn_number} TTFB: LLM={eval_data['llm_ttfb']:.4f}s, STT={eval_data['stt_ttfb']:.4f}s, TTS={eval_data['tts_ttfb']:.4f}s")

                    eval_result = CallEvaluationResultBaseModel(**eval_data)
                    CallEvaluationResultModel.save(eval_result)
                    print(f"   💾 Saved evaluation for turn {turn_number} to database")

                except Exception as e:
                    print(f"   ⚠️ Error saving evaluation to database: {str(e)}")

                # Save to questions_not_found collection if question was not matched (independent save)
                if not question_found and user_question and user_question.strip():
                    try:
                        not_found_data = {
                            "id": ObjectId(),
                            "space_token": space_token,
                            "session_id": session_id,
                            "turn_number": turn_number,
                            "user_question": user_question,
                            "agent_reply": agent_reply if agent_reply else ""
                        }
                        not_found_record = QuestionNotFoundBaseModel(**not_found_data)
                        QuestionNotFoundModel.save(not_found_record)
                        print(f"   📝 Saved unmatched question to questions_not_found collection")
                    except Exception as e:
                        print(f"   ⚠️ Error saving to questions_not_found: {str(e)}")

                evaluations.append(evaluation)
                print(f"   📊 Evaluation: Similarity={similarity:.1%}, Relevancy={relevancy:.1%}, "
                      f"Completeness={completeness:.1%}, Accuracy={accuracy:.1%}")

                # If we didn't find a match, try to find similar questions
                if not matched_qa and user_question:
                    print(f"   ℹ️ No matching QA pair found, looking for similar questions")
                    try:
                        similarities = []
                        for qa in self.ground_truth:
                            if 'question' in qa and 'answer' in qa:
                                sim = self._calculate_similarity(user_question, qa['question'])
                                similarities.append((sim, qa))

                        if similarities:
                            best_sim, best_qa = max(similarities, key=lambda x: x[0])
                            if best_sim > 0.3:  # Only use if there's some similarity
                                eval_question = best_qa.get('question', 'No question')
                                expected_output = best_qa.get('answer', 'No answer')
                                similarity = best_sim
                                relevancy = self._calculate_relevancy(agent_reply, expected_output)
                                completeness = self._calculate_completeness(agent_reply, expected_output)
                                accuracy = self._calculate_accuracy(agent_reply, expected_output)
                                matched_keywords = [k for k in best_qa.get('keywords', [])
                                                  if k.lower() in user_question.lower()]
                                print(f"   ℹ️ Using similar question: {eval_question[:80]}...")
                    except Exception as e:
                        print(f"   ⚠️ Error finding similar questions: {str(e)}")

                print(f"   📊 Scores: Similarity={similarity:.2f}, Relevancy={relevancy:.2f}, "
                      f"Completeness={completeness:.2f}, Accuracy={accuracy:.2f}")

            # After all evaluations, calculate and save quality metrics
            if evaluations:
                self.calculate_quality_metrics(session_id, space_token=space_token)

        except Exception as e:
            print(f"❌ Database error during evaluation: {e}")
            raise

        print(f"\n✅ Evaluation complete: {len(evaluations)} turns evaluated")
        return evaluations

    def calculate_quality_metrics(self, session_id: str, space_token: Optional[str] = None):
        """Calculate aggregate quality metrics for a session using MongoDB"""
        try:
            # Get conversation turn metrics
            turns = list(ConversationTurnModel.find(session_id=session_id))
            total_turns = len(turns)

            response_times = [t.voice_to_voice_response_time for t in turns
                            if t.voice_to_voice_response_time is not None]

            avg_response = sum(response_times) / len(response_times) if response_times else 0.0

            # Get evaluation metrics
            evals = list(CallEvaluationResultModel.find(session_id=session_id))

            if evals:
                avg_similarity = sum(e.similarity for e in evals) / len(evals)
                avg_relevancy = sum(e.relevancy for e in evals) / len(evals)
                avg_completeness = sum(e.completeness for e in evals) / len(evals)
                avg_accuracy = sum(e.accuracy for e in evals) / len(evals)
                questions_matched = len(evals)
            else:
                avg_similarity = 0.0
                avg_relevancy = 0.0
                avg_completeness = 0.0
                avg_accuracy = 0.0
                questions_matched = 0

            # Calculate overall quality score
            overall_quality = (avg_relevancy * 0.4 + avg_completeness * 0.3 + avg_accuracy * 0.3)

            # Save metrics to MongoDB
            metrics_data = {
                "space_token": space_token,
                "session_id": session_id,
                "total_turns": total_turns,
                "avg_response_time": avg_response,
                "avg_similarity": avg_similarity,
                "avg_relevancy": avg_relevancy,
                "avg_completeness": avg_completeness,
                "avg_accuracy": avg_accuracy,
                "questions_matched": questions_matched,
                "overall_quality": overall_quality
            }

            # Check if metrics already exist for this session using get()
            existing = None
            try:
                existing = CallQualityMetricsModel.get(session_id=session_id)
            except DoesNotExistError:
                existing = None  # Document doesn't exist, will create new

            if existing:
                CallQualityMetricsModel._get_collection().update_one(
                    {"session_id": session_id},
                    {"$set": metrics_data}
                )
            else:
                # Add id for MongoDB
                metrics_data["id"] = ObjectId()
                metrics = CallQualityMetricsBaseModel(**metrics_data)
                CallQualityMetricsModel.save(metrics)

            metrics = {
                'total_turns': total_turns,
                'avg_response_time': avg_response,
                'avg_similarity': avg_similarity,
                'avg_relevancy': avg_relevancy,
                'avg_completeness': avg_completeness,
                'avg_accuracy': avg_accuracy,
                'questions_matched': questions_matched,
                'overall_quality_score': overall_quality
            }

            print(f"\n📊 Quality Metrics Summary:")
            print(f"   Total turns: {total_turns}")
            print(f"   Avg response time: {avg_response:.3f}s")
            print(f"   Questions matched: {questions_matched}/{total_turns}")
            print(f"   Overall quality score: {overall_quality:.2f}")

            return metrics

        except Exception as e:
            print(f"❌ Error calculating quality metrics: {e}")
            return {}


# Main evaluation function (use this in your workflow)
async def evaluate_voice_call(
        session_id: str,
        agent_id: str,
        transcript: List[Dict],
        audio_data: Optional[bytes] = None,
        turn_metrics: Optional[Dict] = None,
        space_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main function to evaluate a voice call
    This is what you'll call from your voice bot

    Args:
        session_id: Unique session identifier
        agent_id: Agent identifier
        transcript: List of conversation messages with role and content
        audio_data: Optional audio recording bytes
        turn_metrics: Optional dictionary containing per-turn cost and latency metrics from observer
        space_token: Optional space token for tracking which space this call belongs to

    Returns:
        Dictionary with evaluation results and metrics
    """
    try:
        # Pass agent_id to load QA pairs from MongoDB
        evaluator = VoiceCallEvaluator(agent_id=agent_id)
    except Exception as e:
        print(f"❌ Error creating VoiceCallEvaluator: {e}")
        import traceback
        traceback.print_exc()
        return {
            'session_id': session_id,
            'evaluation_results': [],
            'quality_metrics': {},
            'audio_file_path': None
        }

    try:
        call_start_time = time.time()

        # Step 1: Save conversation turns
        print("📝 Saving conversation turns...")
        turn_number = 0
        i = 0
        while i < len(transcript):
            msg = transcript[i]
            role = msg.get('role', '').lower()
            content = str(msg.get('content', '')).strip()

            # Get timestamp or use current time
            timestamp = msg.get('timestamp', time.time())
            if isinstance(timestamp, str):
                try:
                    # Try to parse ISO format timestamp first
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamp = dt.timestamp()
                except (ValueError, TypeError):
                    try:
                        # Try direct float conversion
                        timestamp = float(timestamp)
                    except (ValueError, TypeError):
                        timestamp = time.time()

            turn_number += 1

            if role == 'user' and i + 1 < len(transcript) and transcript[i+1].get('role', '').lower() == 'assistant':
                # This is a user message followed by an assistant message
                next_msg = transcript[i+1]
                next_content = str(next_msg.get('content', '')).strip()
                next_timestamp = next_msg.get('timestamp', timestamp + 1.0)
                if isinstance(next_timestamp, str):
                    try:
                        # Try to parse ISO format timestamp first
                        dt = datetime.fromisoformat(next_timestamp.replace('Z', '+00:00'))
                        next_timestamp = dt.timestamp()
                    except (ValueError, TypeError):
                        try:
                            # Try direct float conversion
                            next_timestamp = float(next_timestamp)
                        except (ValueError, TypeError):
                            next_timestamp = timestamp + 1.0

                response_time = next_timestamp - timestamp if next_timestamp > timestamp else 1.0

                evaluator.save_conversation_turn(
                    session_id=session_id,
                    turn_number=turn_number,
                    turn_start_time=timestamp,
                    turn_end_time=next_timestamp,
                    user_speech_text=content,
                    llm_response_text=next_content,
                    voice_to_voice_response_time=response_time,
                    interrupted=False,
                    space_token=space_token
                )
                i += 2  # Skip the assistant message in the next iteration
            else:
                # This is a standalone message (user, assistant, or system)
                evaluator.save_conversation_turn(
                    session_id=session_id,
                    turn_number=turn_number,
                    turn_start_time=timestamp,
                    turn_end_time=timestamp + 1.0,  # 1 second duration for standalone messages
                    user_speech_text=content if role == 'user' else '',
                    llm_response_text=content if role in ['assistant', 'system'] else '',
                    voice_to_voice_response_time=0.0,
                    interrupted=True,
                    space_token=space_token
                )
                i += 1

        call_end_time = time.time()

        # Step 2: Save audio if provided
        audio_path = None
        if audio_data:
            print("🔊 Saving audio recording...")
            audio_path = evaluator.save_audio_recording(session_id, audio_data)

        # Step 2.5: Extract and save audio chunks per turn
        if audio_path and os.path.exists(audio_path):
            print("🎵 Extracting audio chunks for each turn...")
            try:
                # Get turns from MongoDB
                turns = list(ConversationTurnModel.find(session_id=session_id))

                for turn in turns:
                    # Extract audio chunk for this turn
                    audio_chunk = evaluator.extract_audio_chunk(
                        audio_path,
                        turn.turn_start_time,
                        turn.turn_end_time
                    )
                    if audio_chunk:
                        # Update the turn with audio data using pymongo collection directly
                        ConversationTurnModel._get_collection().update_one(
                            {"session_id": session_id, "turn_number": turn.turn_number},
                            {"$set": {"wav_audio": audio_chunk}}
                        )
                        print(f"   ✅ Saved audio chunk for turn {turn.turn_number} ({len(audio_chunk)} bytes)")

            except Exception as e:
                print(f"   ⚠️ Error saving audio chunks: {e}")

        # Step 3: Save call session
        print("💾 Saving call session...")
        evaluator.save_call_session(
            session_id=session_id,
            agent_id=agent_id,
            call_start_time=call_start_time,
            call_end_time=call_end_time,
            transcript=transcript,
            audio_file_path=audio_path,
            space_token=space_token
        )

        # Step 4: Evaluate call quality
        print("🔍 Evaluating call quality...")
        if turn_metrics:
            print(f"📊 Turn metrics available: {len(turn_metrics)} turns - keys: {list(turn_metrics.keys())}")
        else:
            print("⚠️ No turn metrics provided for evaluation")
        evaluation_results = await evaluator.evaluate_call_quality(session_id, transcript, turn_metrics=turn_metrics, space_token=space_token)

        # Step 5: Calculate metrics
        print("📊 Calculating quality metrics...")
        quality_metrics = evaluator.calculate_quality_metrics(session_id, space_token=space_token)

        return {
            'session_id': session_id,
            'evaluation_results': evaluation_results,
            'quality_metrics': quality_metrics,
            'audio_file_path': audio_path
        }
    except Exception as e:
        print(f"❌ Error in evaluate_voice_call: {e}")
        import traceback
        traceback.print_exc()
        return {
            'session_id': session_id,
            'evaluation_results': [],
            'quality_metrics': {},
            'audio_file_path': None
        }


if __name__ == "__main__":
    print("🚀 Voice Call Evaluator - Independent System (MongoDB)")
    print("=" * 80)
    print("✅ Ready to evaluate voice calls!")
    print("\n📁 Database: MongoDB")
    print("🔊 Recordings: db-and-recordings/")
    print("\n💡 Usage:")
    print("   from voice_evaluation import evaluate_voice_call")
    print("   result = await evaluate_voice_call(session_id, agent_id, transcript)")
