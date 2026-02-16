"""
MongoDB Models for Voice Agent Evaluations
Migrated from SQLite to MongoDB using mongomantic
"""
from typing import Optional, Dict, List
from datetime import datetime
from mongomantic import BaseRepository, MongoDBModel, Index
from pydantic import Field

from super_services.libs.core.mixin import CreateUpdateMixinModel


class CallSessionBaseModel(MongoDBModel, CreateUpdateMixinModel):
    """Call session metadata - equivalent to SQLite call_session table"""
    space_token: Optional[str] = Field(default=None)
    session_id: str = Field(...)
    agent_id: Optional[str] = Field(default=None)
    call_start_time: float = Field(...)
    call_end_time: float = Field(...)
    duration: Optional[float] = Field(default=None)
    audio_file_path: Optional[str] = Field(default=None)
    transcript: Optional[str] = Field(default=None)  # JSON string


class CallSessionModel(BaseRepository):
    class Meta:
        model = CallSessionBaseModel
        collection = "voice_call_sessions"
        indexes = [
            Index(fields=["session_id"], unique=True),
            Index(fields=["agent_id"]),
            Index(fields=["call_start_time"]),
        ]


class ConversationTurnBaseModel(MongoDBModel, CreateUpdateMixinModel):
    """Individual conversation turns - equivalent to SQLite conversation_turn table"""
    space_token: Optional[str] = Field(default=None)
    session_id: str = Field(...)
    turn_number: int = Field(...)
    turn_start_time: Optional[float] = Field(default=None)
    turn_end_time: Optional[float] = Field(default=None)
    user_speech_text: Optional[str] = Field(default=None)
    llm_response_text: Optional[str] = Field(default=None)
    voice_to_voice_response_time: Optional[float] = Field(default=None)
    interrupted: bool = Field(default=False)
    wav_audio: Optional[bytes] = Field(default=None)  # Binary audio data


class ConversationTurnModel(BaseRepository):
    class Meta:
        model = ConversationTurnBaseModel
        collection = "voice_conversation_turns"
        indexes = [
            Index(fields=["session_id"]),
            Index(fields=["turn_number"]),
        ]


class CallEvaluationResultBaseModel(MongoDBModel, CreateUpdateMixinModel):
    """Per-turn evaluation metrics - equivalent to SQLite call_evaluation_result table"""
    space_token: Optional[str] = Field(default=None)
    session_id: str = Field(...)
    turn_number: int = Field(...)
    user_question: Optional[str] = Field(default=None)
    eval_question: Optional[str] = Field(default=None)
    question_found: bool = Field(default=False)  # True if user question matched with QA pairs
    agent_reply: Optional[str] = Field(default=None)
    expected_output: Optional[str] = Field(default=None)
    similarity: float = Field(default=0.0)
    relevancy: float = Field(default=0.0)
    completeness: float = Field(default=0.0)
    accuracy: float = Field(default=0.0)
    overall_quality: float = Field(default=0.0)
    matched_keywords: Optional[str] = Field(default=None)  # JSON string

    # Per-turn cost tracking
    llm_cost: Optional[float] = Field(default=0.0)
    stt_cost: Optional[float] = Field(default=0.0)
    tts_cost: Optional[float] = Field(default=0.0)

    # Per-turn usage tracking
    llm_prompt_tokens: Optional[int] = Field(default=0)
    llm_completion_tokens: Optional[int] = Field(default=0)
    stt_duration: Optional[float] = Field(default=0.0)  # seconds
    tts_characters: Optional[int] = Field(default=0)

    # Per-turn latency tracking (in milliseconds)
    llm_latency: Optional[float] = Field(default=0.0)
    stt_latency: Optional[float] = Field(default=0.0)
    tts_latency: Optional[float] = Field(default=0.0)

    # Per-turn TTFB (Time To First Byte) in seconds
    llm_ttfb: Optional[float] = Field(default=0.0)
    stt_ttfb: Optional[float] = Field(default=0.0)
    tts_ttfb: Optional[float] = Field(default=0.0)


class CallEvaluationResultModel(BaseRepository):
    class Meta:
        model = CallEvaluationResultBaseModel
        collection = "voice_call_evaluation_results"
        indexes = [
            Index(fields=["session_id"]),
            Index(fields=["turn_number"]),
            Index(fields=["overall_quality"]),
        ]


class QuestionNotFoundBaseModel(MongoDBModel, CreateUpdateMixinModel):
    """Questions that were not found in QA pairs - for improving QA database"""
    space_token: Optional[str] = Field(default=None)
    session_id: str = Field(...)
    turn_number: int = Field(...)
    user_question: str = Field(...)
    agent_reply: Optional[str] = Field(default=None)


class QuestionNotFoundModel(BaseRepository):
    class Meta:
        model = QuestionNotFoundBaseModel
        collection = "voice_questions_not_found"
        indexes = [
            Index(fields=["session_id"]),
            Index(fields=["user_question"]),
        ]


class CallQualityMetricsBaseModel(MongoDBModel, CreateUpdateMixinModel):
    """Session-level aggregate metrics - equivalent to SQLite call_quality_metrics table"""
    space_token: Optional[str] = Field(default=None)
    session_id: str = Field(...)
    total_turns: int = Field(default=0)
    avg_response_time: Optional[float] = Field(default=None)
    avg_similarity: Optional[float] = Field(default=None)
    avg_relevancy: Optional[float] = Field(default=None)
    avg_completeness: Optional[float] = Field(default=None)
    avg_accuracy: Optional[float] = Field(default=None)
    questions_matched: int = Field(default=0)
    overall_quality: Optional[float] = Field(default=None)


class CallQualityMetricsModel(BaseRepository):
    class Meta:
        model = CallQualityMetricsBaseModel
        collection = "voice_call_quality_metrics"
        indexes = [
            Index(fields=["session_id"], unique=True),
            Index(fields=["overall_quality"]),
        ]
