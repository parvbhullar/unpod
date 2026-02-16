"""
Voice processors module.

Contains frame processors for the voice pipeline including:
- StreamingTextParser: Parses streaming LLM responses for early TTS synthesis
- RAGProcessor: Synchronous context enrichment for low-latency RAG
- SilenceTrimmerProcessor: Trims leading silence from TTS audio
"""

from super.core.voice.processors.streaming_text_parser import (
    StreamingTextParser,
    StreamingTextParserProcessor,
    ParseState,
)
from super.core.voice.processors.rag_processor import (
    RAGProcessor,
    create_rag_processor,
)
from super.core.voice.processors.silence_trimmer import (
    SilenceTrimmerProcessor,
    create_silence_trimmer,
)

__all__ = [
    "StreamingTextParser",
    "StreamingTextParserProcessor",
    "ParseState",
    "RAGProcessor",
    "create_rag_processor",
    "SilenceTrimmerProcessor",
    "create_silence_trimmer",
]
