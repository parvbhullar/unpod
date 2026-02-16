"""
Batch Evaluation Script for Voice Recordings - MongoDB Version

This script processes all audio recordings in the db-and-recordings directory,
evaluates them, and saves the results to MongoDB.
"""

import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from voice_evaluation import VoiceCallEvaluator, evaluate_voice_call

# MongoDB imports - Import OID patch first for Pydantic v2 compatibility
from super_services.libs.core.model import *  # This applies the OID patch
from super_services.db.services import *  # This initializes the connection
from super_services.db.services.models.voice_evaluation import (
    CallSessionModel, CallSessionBaseModel,
    ConversationTurnModel, ConversationTurnBaseModel,
    CallEvaluationResultModel,
    CallQualityMetricsModel
)
from bson import ObjectId


def parse_timestamp(timestamp: Union[str, float, int]) -> datetime:
    """
    Parse a timestamp that could be in ISO format or a float representing seconds.

    Args:
        timestamp: Either an ISO format string or a float/int representing seconds

    Returns:
        datetime: The parsed datetime object
    """
    if isinstance(timestamp, (int, float)):
        # Handle float/int timestamps (from Whisper)
        return datetime.utcfromtimestamp(timestamp)
    elif isinstance(timestamp, str):
        # Handle ISO format strings (from transcript files)
        return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    else:
        raise ValueError(f"Unsupported timestamp format: {type(timestamp)}")


class BatchRecordingEvaluator:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.recordings_dir = self.base_dir / "db-and-recordings"
        self.evaluator = VoiceCallEvaluator(recordings_dir=str(self.recordings_dir))
        # Ensure the directory exists
        self.recordings_dir.mkdir(parents=True, exist_ok=True)
        print("✅ BatchRecordingEvaluator initialized with MongoDB")

    def get_unprocessed_recordings(self) -> List[Path]:
        """Get list of WAV files that haven't been processed yet."""
        # Get all WAV files in recordings directory (case insensitive)
        all_recordings = list(self.recordings_dir.glob("*.wav")) + list(self.recordings_dir.glob("*.WAV"))

        # Get list of already processed recordings from MongoDB
        processed_audio_files = set()
        processed_session_ids = set()

        try:
            # Get all sessions - mongomantic uses keyword args
            sessions = list(CallSessionModel.find())
            for session in sessions:
                if session.audio_file_path:
                    processed_audio_files.add(session.audio_file_path.lower())
                if session.session_id:
                    processed_session_ids.add(session.session_id.lower())

        except Exception as e:
            print(f"Error querying database: {e}")
            # If we can't check the database, assume no recordings are processed
            return all_recordings

        # Return only unprocessed recordings
        unprocessed = []
        for recording in all_recordings:
            # Extract session_id from filename (format: {session_id}_YYYYMMDD_HHMMSS.wav)
            try:
                session_id = recording.stem.split('_')[0]
                if (recording.name.lower() not in processed_audio_files and
                    session_id.lower() not in processed_session_ids):
                    unprocessed.append(recording)
            except Exception as e:
                print(f"Error processing {recording.name}: {e}")
                continue

        return unprocessed

    async def _extract_transcript(self, audio_path: Path) -> List[Dict]:
        """
        Extract transcript from audio file or use the provided transcript.

        Priority order:
        1. Check MongoDB for existing transcript (from post_call.py)
        2. Check for transcript JSON file
        3. Fall back to Whisper transcription

        Args:
            audio_path: Path to the audio file

        Returns:
            List of transcript segments with role, content, and timestamp
        """
        try:
            print(f"🔍 Processing audio file: {audio_path}")
            print(f"📁 File exists: {audio_path.exists()}")
            print(f"📁 File size: {audio_path.stat().st_size} bytes" if audio_path.exists() else "File does not exist")

            # Extract session ID from filename
            session_id = audio_path.stem.split('_')[0]

            # PRIORITY 1: Check MongoDB for existing transcript (from post_call.py or previous runs)
            print(f"🔍 Step 1: Checking MongoDB for existing transcript...")
            try:
                session = CallSessionModel.get(session_id=session_id)
                if session and session.transcript:
                    try:
                        transcript_data = json.loads(session.transcript)
                        if transcript_data and isinstance(transcript_data, list) and len(transcript_data) > 0:
                            print(f"✅ Found transcript in MongoDB with {len(transcript_data)} segments")
                            return transcript_data
                    except json.JSONDecodeError as e:
                        print(f"⚠️ Error parsing transcript from database: {e}")
            except Exception as e:
                print(f"⚠️ Error checking database for transcript: {e}")

            print("ℹ️ No transcript found in database")

            # PRIORITY 2: Check for transcript JSON file
            transcript_file = self.recordings_dir / f"{session_id}_transcript.json"
            print(f"🔍 Step 2: Looking for transcript file: {transcript_file}")
            print(f"📄 Transcript file exists: {transcript_file.exists()}")

            if transcript_file.exists():
                try:
                    with open(transcript_file, 'r', encoding='utf-8') as f:
                        transcript_data = json.load(f)
                        print(f"✅ Loaded transcript from JSON file with {len(transcript_data.get('transcript', []))} segments")
                        return transcript_data.get('transcript', [])
                except Exception as e:
                    print(f"⚠️ Error loading transcript file: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("ℹ️ No transcript file found")

            # PRIORITY 3: Fall back to Whisper if no transcript is found
            print("🔊 Step 3: Attempting to transcribe audio with Whisper (lowest quality, slowest)...")
            try:
                import whisper
                import torch

                device = "cuda" if torch.cuda.is_available() else "cpu"
                print(f"⚙️ Using device: {device}")

                # Check if audio file is accessible
                if not audio_path.exists():
                    raise FileNotFoundError(f"Audio file not found: {audio_path}")

                # Using tiny model for fastest CPU processing (lower accuracy but much faster)
                print("⚡ Loading Whisper tiny model (fastest on CPU, lower accuracy)...")
                model = whisper.load_model("tiny").to(device)

                # Transcribe audio
                print(f"🎤 Transcribing audio: {audio_path}")
                result = model.transcribe(str(audio_path))

                # Format transcript
                transcript = []
                for segment in result.get('segments', []):
                    transcript.append({
                        'role': 'user',  # Assuming all audio is user speech
                        'content': segment['text'].strip(),
                        'timestamp': segment['start']
                    })

                print(f"✅ Transcription complete: {len(transcript)} segments")
                return transcript

            except Exception as e:
                print(f"❌ Error during transcription: {e}")
                import traceback
                traceback.print_exc()
                print("⚠️ No transcript could be generated")
                return []

        except Exception as e:
            print(f"❌ Error in _extract_transcript: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def _process_turn(self, session_id: str, turn_number: int, role: str,
                     content: str, timestamp: float) -> None:
        """
        Process a single conversation turn and save it to MongoDB.

        Args:
            session_id: ID of the session
            turn_number: Turn number in the conversation
            role: Role of the speaker ('user' or 'assistant')
            content: Text content of the turn
            timestamp: Timestamp of the turn
        """
        print(f"🔧 Processing turn {turn_number} for session {session_id}")
        print(f"📝 Role: {role}, Timestamp: {timestamp}, Content: {content[:50]}...")

        try:
            # Check if turn already exists - use get()
            existing = ConversationTurnModel.get(
                session_id=session_id,
                turn_number=turn_number
            )

            # Get the previous turn to link user questions with assistant responses
            prev_turn = None
            if turn_number > 1:
                prev_turn = ConversationTurnModel.get(
                    session_id=session_id,
                    turn_number=turn_number - 1
                )

            turn_data = {
                "session_id": session_id,
                "turn_number": turn_number,
                "turn_start_time": timestamp - 5,  # 5 seconds before the response
                "turn_end_time": timestamp,
                "user_speech_text": content if role == 'user' else (prev_turn.user_speech_text if prev_turn else ''),
                "llm_response_text": content if role == 'assistant' else '',
                "voice_to_voice_response_time": 5.0,
                "interrupted": False,
                "wav_audio": None
            }

            if existing:
                ConversationTurnModel._get_collection().update_one(
                    {"session_id": session_id, "turn_number": turn_number},
                    {"$set": turn_data}
                )
            else:
                # Add id for MongoDB
                turn_data["id"] = ObjectId()
                turn = ConversationTurnBaseModel(**turn_data)
                ConversationTurnModel.save(turn)

            print(f"✅ Turn {turn_number} saved successfully")
        except Exception as e:
            print(f"❌ Error processing turn {turn_number}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

    async def run(self):
        """Process all unprocessed recordings."""
        unprocessed = self.get_unprocessed_recordings()
        if not unprocessed:
            print("✅ No unprocessed recordings found.")
            return

        print(f"🔍 Found {len(unprocessed)} unprocessed recordings")

        for audio_path in unprocessed:
            try:
                result = await self.process_recording(audio_path)
                if result.get('status') == 'success':
                    print(f"✅ Successfully processed {audio_path.name}")
                else:
                    print(f"❌ Failed to process {audio_path.name}: {result.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"❌ Error processing {audio_path.name}: {str(e)}")
                import traceback
                traceback.print_exc()

    async def process_recording(self, audio_path: Path) -> Dict:
        """Process a single audio recording and store evaluation results."""
        session_id = audio_path.stem.split('_')[0]  # Extract session ID from filename
        agent_id = "vajiram-ravi-bot"
        turns_processed = 0

        print(f"\n🔄 Processing recording: {audio_path.name}")
        print(f"📝 Session ID: {session_id}")

        try:
            # Extract transcript from audio
            print(f"🔍 Extracting transcript...")
            transcript = await self._extract_transcript(audio_path)

            if not transcript:
                print(f"❌ No transcript returned for {audio_path.name}")
                return {"status": "failed", "error": "No transcript returned", "session_id": session_id}

            if len(transcript) < 2:
                print(f"⚠️ Transcript is too short (only {len(transcript)} segments), but will try to process anyway")

            print(f"📄 Transcript contains {len(transcript)} segments")

            # Calculate call duration (in seconds)
            start_time = parse_timestamp(transcript[0]["timestamp"]) if transcript else datetime.now()
            end_time = parse_timestamp(transcript[-1]["timestamp"]) if transcript else datetime.now()
            duration = (end_time - start_time).total_seconds()

            print(f"⏱️  Call duration: {duration:.2f} seconds")

            # Save call session to MongoDB
            session_data = {
                "session_id": session_id,
                "agent_id": agent_id,
                "call_start_time": start_time.timestamp(),
                "call_end_time": end_time.timestamp(),
                "duration": duration,
                "audio_file_path": str(audio_path),
                "transcript": json.dumps(transcript) if transcript else None
            }

            existing_session = CallSessionModel.get(session_id=session_id)
            if existing_session:
                CallSessionModel._get_collection().update_one(
                    {"session_id": session_id},
                    {"$set": session_data}
                )
            else:
                # Add id for MongoDB
                session_data["id"] = ObjectId()
                session = CallSessionBaseModel(**session_data)
                CallSessionModel.save(session)

            # Process each turn in the transcript
            print(f"📊 Transcript segments to process: {len(transcript)}")
            for i, segment in enumerate(transcript, 1):
                # Determine if it's a user or assistant turn (alternating)
                role = "assistant" if i % 2 == 0 else "user"

                # Extract text and timestamp from the segment
                text = segment.get('content', '').strip()
                timestamp = segment.get('timestamp', 0)

                # Log the raw segment for debugging
                print(f"🔍 Raw segment {i}:")
                print(f"   Text: {text}")
                print(f"   Timestamp: {timestamp}")
                print(f"   Role: {role}")

                # Skip empty segments
                if not text:
                    print("   ⚠️ Empty text, skipping...")
                    continue

                print(f"🔊 Processing turn {i} ({role}): {text[:50]}...")

                await self._process_turn(
                    session_id=session_id,
                    turn_number=i,
                    role=role,
                    content=text,
                    timestamp=timestamp
                )
                turns_processed += 1

            # Extract and save audio chunks for each turn
            print(f"\n🎵 Extracting audio chunks for each turn from {audio_path.name}...")
            try:
                import wave
                import io

                # Read all turns from MongoDB to get timestamps - use keyword args
                turns = list(ConversationTurnModel.find(session_id=session_id))
                turns.sort(key=lambda x: x.turn_number)

                with wave.open(str(audio_path), 'rb') as wav_file:
                    framerate = wav_file.getframerate()
                    n_channels = wav_file.getnchannels()
                    sampwidth = wav_file.getsampwidth()

                    for turn in turns:
                        try:
                            # Calculate frame positions
                            start_frame = int(turn.turn_start_time * framerate)
                            end_frame = int(turn.turn_end_time * framerate)

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

                            audio_chunk = output.getvalue()

                            # Update the turn with audio data in MongoDB using pymongo collection
                            ConversationTurnModel._get_collection().update_one(
                                {"session_id": session_id, "turn_number": turn.turn_number},
                                {"$set": {"wav_audio": audio_chunk}}
                            )

                            print(f"   ✅ Saved audio chunk for turn {turn.turn_number} ({len(audio_chunk)} bytes)")

                        except Exception as e:
                            print(f"   ⚠️ Error extracting audio for turn {turn.turn_number}: {e}")

                print(f"✅ Audio chunks saved for all {len(turns)} turns")

            except Exception as e:
                print(f"❌ Error processing audio chunks: {e}")
                import traceback
                traceback.print_exc()

            # Now evaluate the entire conversation
            print(f"\n🔍 Evaluating entire conversation for session {session_id}...")
            try:
                # Audio chunks are already saved to database, no need to pass audio_data
                evaluation_result = await evaluate_voice_call(
                    session_id=session_id,
                    agent_id=agent_id,
                    transcript=transcript,
                    audio_data=None  # Audio chunks already saved in conversation_turn collection
                )

                print(f"✅ Evaluation completed:")
                print(f"   - Session ID: {evaluation_result.get('session_id')}")
                print(f"   - Evaluation results: {len(evaluation_result.get('evaluation_results', []))} items")
                print(f"   - Quality metrics: {evaluation_result.get('quality_metrics', {})}")

            except Exception as e:
                print(f"⚠️ Evaluation failed (data still saved): {e}")
                import traceback
                traceback.print_exc()

            return {
                "status": "success",
                "session_id": session_id,
                "turns_processed": turns_processed
            }

        except Exception as e:
            print(f"❌ Error processing {audio_path.name}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}


async def main():
    evaluator = BatchRecordingEvaluator()
    await evaluator.run()


if __name__ == "__main__":
    asyncio.run(main())
