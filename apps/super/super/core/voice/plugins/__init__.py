"""
Voice Pipeline Plugins - Modular components for voice processing.

This package provides a plugin-based architecture for extending the voice pipeline
with optional features like RAG, streaming parsing, and transcript handling.

Available plugins:
    - rag: RAG context enrichment (PRE_LLM priority)
    - transcript: Transcript processing and storage (LAST priority)
    - streaming: Streaming JSON parser for TTS (POST_LLM priority)
    - silence: Silence trimmer for TTS audio (POST_TTS priority)
    - idle: User idle detection (LAST priority)
    - filler: Quick conversational filler generation (PRE_LLM priority)
"""

from super.core.voice.plugins.base import (
    PipelinePlugin,
    PluginConfig,
    PluginPriority,
)
from super.core.voice.plugins.registry import PluginRegistry

__all__ = [
    "PipelinePlugin",
    "PluginConfig",
    "PluginPriority",
    "PluginRegistry",
]
