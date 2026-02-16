"""
SuperKik Voice Agent - Voice-first service discovery and booking assistant.

SuperKik extends the LiveKit voice framework to provide:
- Provider discovery via Google Places API
- Web search and event discovery via Exa
- People search (LinkedIn, social profiles) via Exa
- Real-time recommendation card streaming
- Direct call patching to providers
- Voice-based booking with natural language
- User preference memory
- Smart intent classification

Usage:
    Set AGENT_PROVIDER=superkik to enable this handler.

Example (Native Bindings - Recommended):
    from super.core.voice.superkik import SuperkikAgentHandler
    from livekit.agents import cli, WorkerOptions

    handler = SuperkikAgentHandler(session_id="session_123")
    cli.run_app(WorkerOptions(entrypoint_fnc=handler.entrypoint))

Example (Legacy Pipecat):
    from super.core.voice.superkik import SuperKikHandler

    handler = SuperKikHandler(
        session_id="session_123",
        user_state=user_state,
        model_config=config,
    )
    await handler.preload_agent(user_state, observer)
    await handler.execute_with_context(ctx)

Config-based Prompt Customization:
    config = {
        "superkik": {
            "system_prompt": "Your custom prompt...",  # Optional
            "use_compact_prompt": True,  # Use compact version
        }
    }
"""

from super.core.voice.superkik.handler import SuperKikHandler
from super.core.voice.superkik.agent_handler import SuperkikAgentHandler
from super.core.voice.superkik.prompts import (
    SUPERKIK_SYSTEM_PROMPT,
    SUPERKIK_COMPACT_PROMPT,
    get_superkik_prompt,
    build_agent_context,
    classify_intent,
    format_voice_response,
    INTENT_PATTERNS,
    VOICE_RESPONSES,
)
from super.core.voice.superkik.schema import (
    BookingRequest,
    BookingStatus,
    CallStatus,
    EventCard,
    PersonCard,
    ProviderCard,
    SearchRequest,
    SearchResult,
    UserPreferences,
    WebResultCard,
)

__all__ = [
    # Handlers
    "SuperKikHandler",  # Legacy pipecat-based handler
    "SuperkikAgentHandler",  # Native bindings handler (recommended)
    # Prompts
    "SUPERKIK_SYSTEM_PROMPT",
    "SUPERKIK_COMPACT_PROMPT",
    "get_superkik_prompt",
    "build_agent_context",
    "classify_intent",
    "format_voice_response",
    "INTENT_PATTERNS",
    "VOICE_RESPONSES",
    # Schema - Providers
    "ProviderCard",
    "SearchRequest",
    "SearchResult",
    # Schema - Web/People Discovery
    "WebResultCard",
    "PersonCard",
    "EventCard",
    # Schema - Booking/Call
    "BookingRequest",
    "BookingStatus",
    "CallStatus",
    "UserPreferences",
]
