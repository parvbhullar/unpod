#!/usr/bin/env python3
"""
Fetch session data by session_id - MongoDB version

Usage:
    python fetch_session.py <session_id>

Example:
    python fetch_session.py ced498af-de71-453e-abad-92109c1cbef3
"""

import json
import sys

# Initialize MongoDB connection - Import OID patch first for Pydantic v2 compatibility
from super_services.libs.core.model import *  # This applies the OID patch
from super_services.db.services import *  # This initializes the connection
from super_services.db.services.models.voice_evaluation import (
    CallSessionModel,
    ConversationTurnModel,
    CallQualityMetricsModel,
    CallEvaluationResultModel
)


def fetch_session_data(session_id: str) -> dict:
    result = {}

    # 1. Call Session - use get() for mongomantic
    session = CallSessionModel.get(session_id=session_id)
    if session:
        result["call_session"] = {
            "session_id": session.session_id,
            "agent_id": session.agent_id,
            "call_start_time": session.call_start_time,
            "call_end_time": session.call_end_time,
            "duration": session.duration,
            "audio_file_path": session.audio_file_path,
            "transcript": session.transcript,
            "created": str(session.created) if session.created else None
        }

    # 2. Conversation Turns - use keyword args
    turns = list(ConversationTurnModel.find(session_id=session_id))
    turns.sort(key=lambda x: x.turn_number)
    result["conversation_turns"] = [{
        "session_id": t.session_id,
        "turn_number": t.turn_number,
        "turn_start_time": t.turn_start_time,
        "turn_end_time": t.turn_end_time,
        "user_speech_text": t.user_speech_text,
        "llm_response_text": t.llm_response_text,
        "voice_to_voice_response_time": t.voice_to_voice_response_time,
        "interrupted": t.interrupted,
        "wav_audio": f"<{len(t.wav_audio)} bytes>" if t.wav_audio else None,
        "created": str(t.created) if t.created else None
    } for t in turns]

    # 3. Quality Metrics - use get()
    metrics = CallQualityMetricsModel.get(session_id=session_id)
    if metrics:
        result["quality_metrics"] = {
            "session_id": metrics.session_id,
            "total_turns": metrics.total_turns,
            "avg_response_time": metrics.avg_response_time,
            "p50_response_time": metrics.p50_response_time,
            "p95_response_time": metrics.p95_response_time,
            "avg_similarity": metrics.avg_similarity,
            "avg_relevancy": metrics.avg_relevancy,
            "avg_completeness": metrics.avg_completeness,
            "avg_accuracy": metrics.avg_accuracy,
            "questions_matched": metrics.questions_matched,
            "overall_quality": metrics.overall_quality,
            "created": str(metrics.created) if metrics.created else None
        }

    # 4. Evaluation Results - use keyword args
    evals = list(CallEvaluationResultModel.find(session_id=session_id))
    evals.sort(key=lambda x: x.turn_number)
    result["evaluation_results"] = [{
        "session_id": e.session_id,
        "turn_number": e.turn_number,
        "user_question": e.user_question,
        "eval_question": e.eval_question,
        "agent_reply": e.agent_reply,
        "expected_output": e.expected_output,
        "similarity": e.similarity,
        "relevancy": e.relevancy,
        "completeness": e.completeness,
        "accuracy": e.accuracy,
        "overall_quality": e.overall_quality,
        "matched_keywords": e.matched_keywords,
        "created": str(e.created) if e.created else None
    } for e in evals]

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fetch_session.py <session_id>")
        print("Example: python fetch_session.py ced498af-de71-453e-abad-92109c1cbef3")
        sys.exit(1)

    session_id = sys.argv[1]
    data = fetch_session_data(session_id)

    if not data.get("call_session"):
        print(f"Session not found: {session_id}")
        sys.exit(1)

    print(json.dumps(data, indent=2, default=str))
