"""
SuperVoiceAgent - End-to-end voice calling framework based on pipecat-ai

This module provides a complete voice calling orchestration system with:
- Multiple transport support (LiveKit, Small-WebRTC, FastAPI WebSocket)
- Full SIP integration for LiveKit transport
- Unified audio pipeline with codec conversion
- Session management with Redis backing
- Observability and metrics collection
- Pipecat-ai agent pipeline integration

Module Structure:
- pipecat/: Pipecat-based voice handlers and services
- livekit/: LiveKit-based voice handlers and services
- managers/: Manager classes (prompts, knowledge base, transport, etc.)
- plugins/: Plugin system for extensibility
- processors/: Pipecat pipeline processors
- prompts/: Prompt templates
- services/: Service factories
- workflows/: Workflow orchestration and multi-agent patterns
- common/: Shared utilities

Usage:
    Import handlers directly from their modules to avoid circular imports:

    from super.core.voice.voice_agent_handler import VoiceAgentHandler
    from super.core.voice.pipecat.handler import PipecatVoiceHandler
    from super.core.voice.livekit.lite_handler import LiveKitLiteHandler
"""

# Core schema and base classes - these are safe to import at module level
from super.core.voice.schema import (
    UserState,
    AgentConfig,
    CallSession,
    TransportType,
    TaskData,
    CallMeta,
)
from super.core.voice.base import BaseVoiceHandler

__all__ = [
    # Schema
    "UserState",
    "AgentConfig",
    "CallSession",
    "TransportType",
    "TaskData",
    "CallMeta",
    # Base
    "BaseVoiceHandler",
]


def __getattr__(name: str):
    """Lazy import for backward compatibility - avoids circular imports."""
    # Main entrypoint
    if name == "VoiceAgentHandler":
        from super.core.voice.voice_agent_handler import VoiceAgentHandler
        return VoiceAgentHandler

    # Pipecat handlers
    if name == "PipecatVoiceHandler":
        from super.core.voice.pipecat.handler import PipecatVoiceHandler
        return PipecatVoiceHandler
    if name == "LiteVoiceHandler":
        from super.core.voice.pipecat.lite_handler import LiteVoiceHandler
        return LiteVoiceHandler
    if name == "ServiceFactory":
        from super.core.voice.pipecat.services import ServiceFactory
        return ServiceFactory
    if name == "UpPipelineRunner":
        from super.core.voice.pipecat.utils import UpPipelineRunner
        return UpPipelineRunner
    if name == "create_usage":
        from super.core.voice.pipecat.utils import create_usage
        return create_usage
    if name == "get_os_info":
        from super.core.voice.pipecat.utils import get_os_info
        return get_os_info

    # LiveKit handlers
    if name == "LiveKitVoiceHandler":
        from super.core.voice.livekit.handler import LiveKitVoiceHandler
        return LiveKitVoiceHandler
    if name == "LiveKitLiteHandler":
        from super.core.voice.livekit.lite_handler import LiveKitLiteHandler
        return LiveKitLiteHandler
    if name == "LiveKitWebhookHandler":
        from super.core.voice.livekit.inbound_handler import LiveKitWebhookHandler
        return LiveKitWebhookHandler
    if name == "create_event_bridge":
        from super.core.voice.livekit.event_bridge import create_event_bridge
        return create_event_bridge
    if name == "SIPDispatcher":
        from super.core.voice.livekit.sip_dispatcher import SIPDispatcher
        return SIPDispatcher

    # Managers
    if name == "PromptManager":
        from super.core.voice.managers.prompt_manager import PromptManager
        return PromptManager
    if name == "KnowledgeBaseManager":
        from super.core.voice.managers.knowledge_base import KnowledgeBaseManager
        return KnowledgeBaseManager
    if name == "FAISSContextProcessor":
        from super.core.voice.managers.context_processor import FAISSContextProcessor
        return FAISSContextProcessor
    if name == "TransportManager":
        from super.core.voice.managers.transport_manager import TransportManager
        return TransportManager
    if name == "SessionManager":
        from super.core.voice.managers.session_manager import SessionManager
        return SessionManager
    if name == "MetricsCollector":
        from super.core.voice.managers.metrics import MetricsCollector
        return MetricsCollector

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
