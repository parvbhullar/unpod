"""
SuperKik Voice Handler - Voice-first service discovery and booking assistant.

Extends LiveKitLiteHandler to add:
- Provider discovery via Google Places API
- Real-time recommendation card streaming
- Direct call patching to providers
- Voice-based booking with natural language
- User preference memory
- Smart intent classification
- Dynamic tool plugin system
"""

import logging
import os
import random
import re
import time
import uuid
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

from super.core.callback.base import BaseCallback
from super.core.configuration import BaseModelConfig
from super.core.handler.config import (
    ExecutionNature,
    HandlerConfiguration,
    RoleConfiguration,
)
from super.core.logging import logging as app_logging
from super.core.plugin.base import PluginLocation, PluginStorageFormat
from super.core.context.schema import Event, Message, Role, User
from super.core.voice.livekit.lite_handler import (
    LiveKitLiteAgent,
    LiveKitLiteHandler,
    TOPIC_LK_CHAT,
)
from super.core.voice.schema import UserState
from super.core.voice.superkik.prompts import (
    build_agent_context,
    build_session_state_context,
    build_user_context,
    classify_intent,
    format_voice_response,
    get_superkik_prompt,
    PATCH_TRIGGER_PATTERNS,
)
from super.core.voice.superkik.schema import (
    BookingStatus,
    BookingStatusType,
    CallStatus,
    CallStatusType,
    CallContext,
    EventCard,
    PersonCard,
    ProviderCard,
    SearchResult,
    SuperKikConfig,
    UserPreferences,
    WebResultCard,
)
from super.core.voice.superkik.tools import ToolPluginRegistry

# Superkik backbone (optional)
try:
    from super.core.voice.superkik.backbone import SuperkikBackbone

    SUPERKIK_BACKBONE_AVAILABLE = True
except ImportError:
    SUPERKIK_BACKBONE_AVAILABLE = False
    SuperkikBackbone = None  # type: ignore

if TYPE_CHECKING:
    from livekit.agents import JobContext
    from livekit.agents.voice import AgentSession, UserInputTranscribedEvent
    from super.core.orchestrator.three_layer import ThreeLayerOrchestrator
    from super.core.orchestrator.three_layer.events import Event
    from super.core.orchestrator.three_layer.shared_context import SharedContext
    from super.core.orchestrator.react_orc import ReActOrc
    from super.core.voice.superkik.backbone import SuperkikBackbone

# SuperKik-specific data channel topics
# All card types use single unified topic
TOPIC_SUPERKIK_CARDS = "superkik.cards"
# Internal topics (not for frontend cards)
TOPIC_PREFERENCES = "superkik.preferences"
TOPIC_SESSION_STATE = "superkik.session"

# Local response patterns - handled without PA
LOCAL_PATTERNS: Dict[str, Tuple[str, List[str]]] = {
    "greeting": (
        r"^(hi|hello|hey|good\s*(morning|afternoon|evening)|greetings)(\s+there)?[\s!.]*$",
        ["Hello! How can I help you today?", "Hi there! What can I do for you?"],
    ),
    "acknowledgment": (
        r"^(yes|no|okay|ok|sure|got\s*it|alright|fine|yep|nope|yeah|nah)[\s!.]*$",
        ["Got it!", "Understood.", "Okay!"],
    ),
    "thanks": (
        r"^(thanks|thank\s*you|thx|ty|appreciate\s*it)[\s!.]*$",
        ["You're welcome!", "Happy to help!", "Glad I could assist!"],
    ),
    "goodbye": (
        r"^(bye|goodbye|see\s*you|later|take\s*care)[\s!.]*$",
        ["Goodbye! Take care!", "See you later!", "Have a great day!"],
    ),
}


def _try_local_response(input_text: str) -> Optional[str]:
    """
    Try to handle input locally without PA.

    Returns response string if handled locally, None otherwise.
    """
    text = input_text.strip()

    for pattern, responses in LOCAL_PATTERNS.values():
        if re.match(pattern, text, re.IGNORECASE):
            return random.choice(responses)

    return None


@dataclass
class SessionState:
    """
    SuperKik session state for continuity and context.

    Maintains conversation state across turns for smart interactions.
    """

    session_id: str
    current_results: List[ProviderCard] = field(default_factory=list)
    selected_provider: Optional[ProviderCard] = None
    pending_action: Optional[Dict[str, Any]] = None
    active_filters: Dict[str, Any] = field(default_factory=dict)
    active_call_id: Optional[str] = None
    active_booking_id: Optional[str] = None
    turn_count: int = 0
    last_intent: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "current_results_count": len(self.current_results),
            "selected_provider": (
                self.selected_provider.to_dict() if self.selected_provider else None
            ),
            "pending_action": self.pending_action,
            "active_filters": self.active_filters,
            "active_call_id": self.active_call_id,
            "active_booking_id": self.active_booking_id,
            "turn_count": self.turn_count,
            "last_intent": self.last_intent,
        }

    def clear_search(self) -> None:
        """Clear search-related state for new search."""
        self.current_results = []
        self.selected_provider = None
        self.pending_action = None

    def set_pending_action(self, action_type: str, params: Dict[str, Any]) -> None:
        """Set a pending action awaiting confirmation."""
        self.pending_action = {
            "type": action_type,
            "params": params,
            "created_at": datetime.utcnow().isoformat(),
        }

    def clear_pending_action(self) -> None:
        """Clear pending action."""
        self.pending_action = None


class SuperKikAgent(LiveKitLiteAgent):
    """
    SuperKik Agent with dynamically registered tools.

    Tools are registered via ToolPluginRegistry instead of being
    hardcoded as class methods. This enables dynamic tool management.
    """

    def __init__(
        self,
        handler: "SuperKikHandler",
        user_state: UserState,
        instructions: str,
        tools: Optional[List[Callable]] = None,
    ):
        super().__init__(
            handler=handler,
            user_state=user_state,
            instructions=instructions,
            tools=tools,
        )
        self._superkik_handler = handler


class SuperKikHandler(LiveKitLiteHandler):
    """
    SuperKik Voice Handler for service discovery and booking.

    Extends LiveKitLiteHandler with:
    - Provider search via Google Places API
    - Real-time card streaming to frontend
    - Telephony integration for call patching
    - Voice-based booking flow
    - User preference memory
    - Smart session state management
    - Intent classification for faster responses
    - Dynamic tool plugin system
    """

    default_configuration = HandlerConfiguration(
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="super.core.voice.superkik.handler.SuperKikHandler",
        ),
        role=RoleConfiguration(
            name="superkik_handler",
            role="A voice-first assistant for service discovery and booking.",
            cycle_count=0,
            max_task_cycle_count=3,
        ),
        execution_nature=ExecutionNature.AUTO,
    )

    def __init__(
        self,
        session_id: Optional[str] = None,
        user_state: Optional[UserState] = None,
        callback: Optional[BaseCallback] = None,
        model_config: Optional[BaseModelConfig] = None,
        configuration: HandlerConfiguration = default_configuration,
        observer: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(
            session_id=session_id,
            user_state=user_state,
            callback=callback,
            model_config=model_config,
            configuration=configuration,
            observer=observer,
            logger=logger or app_logging.get_logger("superkik.handler"),
        )

        # SuperKik-specific configuration
        self.superkik_config = SuperKikConfig.from_dict(self.config)

        # Session state for conversation continuity
        self._session_state = SessionState(
            session_id=self._session_id or str(uuid.uuid4())[:8]
        )

        # SuperKik state
        self._last_search_result: Optional[SearchResult] = None
        self._current_call: Optional[CallStatus] = None
        self._pending_bookings: Dict[str, BookingStatus] = {}
        self._user_preferences: Optional[UserPreferences] = None

        # Pending message_id for correlating cards with LLM response
        # When cards are sent immediately, store message_id so subsequent text uses same ID
        self._pending_message_id: Optional[str] = None

        # Provider history for "repeat" intents
        self._provider_history: List[Dict[str, Any]] = []

        # SIP manager (lazy initialized)
        self._sip_manager: Optional[Any] = None

        # Tool plugin registry (initialized during preload)
        self._tool_registry: Optional[ToolPluginRegistry] = None

        # Callee mode state (for third-party calls)
        self._is_callee_mode: bool = False
        self._callee_mode_context: Optional[Dict[str, Any]] = None
        # Guard to prevent duplicate mode switch calls
        self._mode_switch_in_progress: bool = False
        # Track last processed SIP status to avoid duplicate processing
        self._last_processed_sip_status: Optional[str] = None
        # SIP participant tracking for audio routing
        self._sip_participant: Optional[Any] = None  # The active SIP callee participant
        self._main_user_participant: Optional[Any] = None  # The main user participant

        # Callee user representation for message attribution
        self._callee_user: Optional[User] = None

        # Structured call context gathering
        self._current_call_context: Optional[CallContext] = None
        self._is_patch_mode: bool = False

        # Call transcript sequencing
        self._call_message_seq: int = 0

        # Three-layer orchestrator (optional, for user mode processing)
        self._three_layer_orc: Optional["ThreeLayerOrchestrator"] = None

        # Shared context for three-layer orchestration (observation layer)
        self._shared_context: Optional["SharedContext"] = None

        # ReActOrc as Planning Agent for three-layer integration
        self._react_orc: Optional["ReActOrc"] = None

        # Superkik backbone (optional agentic backbone)
        self._backbone: Optional["SuperkikBackbone"] = None

        self._logger.info(f"SuperKikHandler created (session={self._session_id})")

    @property
    def session_state(self) -> SessionState:
        """Get current session state."""
        return self._session_state

    @property
    def tool_registry(self) -> Optional[ToolPluginRegistry]:
        """Get tool plugin registry."""
        return self._tool_registry

    @property
    def backbone(self) -> Optional["SuperkikBackbone"]:
        """Get superkik backbone if initialized."""
        return self._backbone

    async def preload_agent(
        self,
        user_state: UserState,
        observer: Optional[Any] = None,
    ) -> bool:
        """
        Preload SuperKik agent with tool plugins.

        Args:
            user_state: User state for the session
            observer: Optional observer for metrics

        Returns:
            True if preload successful
        """
        # Check if config is valid, otherwise try default agent
        if not self.config or not self.config.get("agent_id"):
            self._logger.warning("No agent config provided, trying default agent")
            default_config = await self._get_default_agent_config()
            if default_config:
                self.config = default_config
                # Update user_state.model_config for consistency
                user_state.model_config = default_config
                # Re-initialize superkik config with new config
                self.superkik_config = SuperKikConfig.from_dict(self.config)
            else:
                self._logger.error("No agent config and no default agent available")
                return False

        result = await super().preload_agent(user_state, observer)
        if not result:
            return False

        try:
            # Initialize user preferences
            await self._init_user_preferences(user_state)

            # Initialize SIP manager for telephony
            await self._init_sip_manager()

            # Initialize tool plugin registry
            await self._init_tool_registry()

            # Initialize three-layer orchestration if enabled
            if self.superkik_config.enable_orchestrator:
                await self._init_three_layer_orchestrator()
                await self._init_shared_context()

            # Initialize superkik backbone if enabled via env var (alternative to ReActOrc)
            if os.getenv("ENABLE_SUPERKIK_BACKBONE", "").lower() in ("true", "1", "yes"):
                await self._init_superkik_backbone()

            # Load provider history from preferences
            if self._user_preferences:
                self._provider_history = self._user_preferences.history

            self._logger.info("SuperKik preload complete")
            return True

        except Exception as e:
            self._logger.error(f"SuperKik preload failed: {e}")
            return False

    async def _init_tool_registry(self) -> None:
        """Initialize and activate tool plugins."""
        self._tool_registry = ToolPluginRegistry(
            logger=self._logger.getChild("tools"),
        )

        activated = await self._tool_registry.activate_from_config(self, self.config)
        self._logger.info(f"Activated tool plugins: {activated}")

    async def _init_user_preferences(self, user_state: UserState) -> None:
        """Initialize user preferences from storage or create new."""
        if not self.superkik_config.enable_preferences:
            return

        user_id = getattr(user_state, "user_id", None) or str(user_state.thread_id)

        self._user_preferences = UserPreferences(
            user_id=user_id,
            preferred_language=user_state.language,
        )

        if self.superkik_config.default_location:
            self._user_preferences.filters["location"] = list(
                self.superkik_config.default_location
            )

        self._logger.debug(f"User preferences initialized for {user_id}")

    def _get_superkik_config_value(self, key: str, default: Any = None) -> Any:
        """Safely get a value from superkik config."""
        superkik_cfg = self.config.get("superkik", {})
        if isinstance(superkik_cfg, dict):
            return superkik_cfg.get(key, default)
        return default

    async def _get_default_agent_config(self) -> Optional[Dict[str, Any]]:
        """
        Load default agent config from DEFAULT_VOICE_AGENT env var.

        Used as fallback when no agent config is provided.

        Returns:
            Agent config dict or None if not available
        """
        default_agent = os.getenv("DEFAULT_VOICE_AGENT")
        if not default_agent:
            self._logger.warning("DEFAULT_VOICE_AGENT env var not set")
            return None

        try:
            from super_services.voice.models.config import ModelConfig

            config_loader = ModelConfig()
            config = config_loader.get_config(default_agent)

            if config:
                self._logger.info(f"Loaded default agent config: {default_agent}")
                return config

            self._logger.warning(f"No config found for default agent: {default_agent}")
            return None
        except Exception as e:
            self._logger.error(f"Failed to load default agent config: {e}")
            return None

    async def _init_sip_manager(self) -> None:
        """Initialize SIP manager for telephony operations."""
        if not self.superkik_config.enable_call_patching:
            return

        try:
            from super.core.voice.livekit.telephony import SIPManager

            self._sip_manager = SIPManager(
                logger=self._logger.getChild("sip"),
                config=self.config,
                session_id=self._session_id,
                room_name=self._room_name,
                user_state=self.user_state,
            )
            self._logger.debug("SIP manager initialized")

        except Exception as e:
            self._logger.warning(f"SIP manager init failed: {e}")
            self._sip_manager = None

    async def _init_three_layer_orchestrator(self) -> None:
        """Initialize three-layer orchestrator for user mode processing."""
        from super.core.orchestrator.three_layer import ThreeLayerOrchestrator

        self._three_layer_orc = ThreeLayerOrchestrator(
            deliver_callback=self._orchestrator_deliver_callback,
        )
        self._logger.info("[ORCHESTRATOR] ThreeLayerOrchestrator initialized")

    async def _init_shared_context(self) -> None:
        """Initialize SharedContext for three-layer integration."""
        try:
            from super.core.orchestrator.three_layer.shared_context import SharedContext
            from super.core.orchestrator.react_orc import ReActOrc

            self._shared_context = SharedContext()

            # Create ReActOrc as PA
            self._react_orc = ReActOrc()
            self._react_orc.set_shared_context(self._shared_context)

            # Note: ToolPluginRegistry tools (LiveKit function_tools) are not compatible
            # with ReActOrc (expects BaseTool). ReActOrc tools must be registered
            # separately via react_orc.register_tool() with BaseTool instances.

            # Subscribe to context events
            self._subscribe_to_context_events()

            # Load existing thread state if available
            if self.user_state and self.user_state.thread_id:
                await self._shared_context.load_thread_state(str(self.user_state.thread_id))

            self._logger.info("[INIT] SharedContext and ReActOrc initialized")

        except Exception as e:
            self._logger.error(f"[INIT] Failed to initialize SharedContext: {e}")
            # Reset to None on failure to allow graceful degradation
            self._shared_context = None
            self._react_orc = None

    async def _init_superkik_backbone(self) -> None:
        """
        Initialize superkik as agentic backbone.

        Uses the Rust-based superkik binary for reasoning/planning,
        replacing ReActOrc with a more capable agentic framework.
        """
        if not SUPERKIK_BACKBONE_AVAILABLE:
            self._logger.warning(
                "[INIT] Superkik backbone requested but not available. "
                "Install superkik package to enable."
            )
            return

        try:
            self._backbone = SuperkikBackbone(
                handler=self,
                logger=self._logger.getChild("backbone"),
            )

            initialized = await self._backbone.initialize()
            if initialized:
                self._logger.info("[INIT] Superkik backbone initialized successfully")
            else:
                self._logger.warning("[INIT] Superkik backbone initialization failed")
                self._backbone = None

        except Exception as e:
            self._logger.error(f"[INIT] Failed to initialize superkik backbone: {e}")
            self._backbone = None

    async def _orchestrator_deliver_callback(self, response: str) -> None:
        """
        Deliver orchestrator response via TTS and data channel.

        This is called by the orchestrator when it has a response ready.
        Since native agent is bypassed, we manually handle:
        1. Data channel delivery (for frontend text/cards)
        2. TTS synthesis (for voice output)
        """
        self._logger.info(f"[ORCHESTRATOR] Delivering: {response[:100]}...")

        # Send via data channel (reuses existing card correlation)
        await self._handle_voice_response(response)

        # Synthesize TTS (native agent bypassed, so manual TTS needed)
        if self._session:
            try:
                await self._session.say(response, allow_interruptions=True)
            except Exception as e:
                self._logger.error(f"[ORCHESTRATOR] TTS failed: {e}")

    async def _process_via_orchestrator(self, transcript: str) -> None:
        """
        Process user input through three-layer orchestrator.

        Routes user messages through the orchestrator instead of the native
        LiveKit agent for more sophisticated intent handling and response flow.
        """
        if not self._three_layer_orc or not self.user_state:
            self._logger.warning("[ORCHESTRATOR] Not available, skipping")
            return

        thread_id = str(self.user_state.thread_id)
        self._logger.info(f"[ORCHESTRATOR] Processing: {transcript[:50]}...")

        try:
            # Save user message (same as native flow)
            msg = Message.create(
                transcript,
                user=self.user_state,
                event=Event.USER_MESSAGE,
            )
            self._send_callback(msg, thread_id=thread_id)

            # Process through orchestrator
            result = await self._three_layer_orc.process_message(
                thread_id=thread_id,
                input_text=transcript,
            )

            self._logger.info(
                f"[ORCHESTRATOR] Complete: action_id={result['action_id']}, "
                f"intent={result.get('intent')}"
            )

        except Exception as e:
            self._logger.error(f"[ORCHESTRATOR] Processing failed: {e}")
            # Deliver error message to user
            await self._orchestrator_deliver_callback(
                "I'm sorry, I had trouble processing that. Could you try again?"
            )

    async def _route_user_input(self, transcript: str) -> None:
        """
        Route user input through two-tier classification.

        1. Callee/Patch mode: Skip to native handler
        2. Local response: Handle trivially without PA
        3. Complex task: Route to PA via SharedContext
        """
        # Skip routing for callee/patch modes
        if self._is_callee_mode or self._is_patch_mode:
            return

        # Skip if no context configured
        if not self._shared_context:
            self._logger.debug("[ROUTING] No shared context configured, skipping")
            return

        # Try local response first
        local_response = _try_local_response(transcript)
        if local_response:
            self._logger.debug(f"[ROUTING] Local response: {transcript[:30]}...")
            await self._deliver_response(local_response)
            return

        # Route to PA
        self._logger.debug(f"[ROUTING] PA processing: {transcript[:30]}...")
        await self._process_via_pa(transcript)

    def _subscribe_to_context_events(self) -> None:
        """Subscribe to SharedContext events for response delivery."""
        if not self._shared_context:
            return

        from super.core.orchestrator.three_layer.events import EventType

        self._shared_context.subscribe(
            EventType.ACTION_COMPLETED,
            self._on_action_completed
        )
        self._shared_context.subscribe(
            EventType.STATUS_CHANGED,
            self._on_status_changed
        )
        self._shared_context.subscribe(
            EventType.WAITING_FOR_INPUT,
            self._on_waiting_for_input
        )

    async def _on_action_completed(self, event: "Event") -> None:
        """Handle action completion - deliver response."""
        result = event.get("data", {}).get("result", {})
        response = result.get("response")
        if response:
            await self._deliver_response(response)

    async def _on_status_changed(self, event: "Event") -> None:
        """Handle status change - deliver engagement for ASYNC."""
        from super.core.orchestrator.three_layer.models import ActionStatus, ExecutionMode

        action_id = event.get("action_id")
        if not action_id or not self._shared_context:
            return

        action = self._shared_context.get_action(action_id)
        if not action:
            return

        new_status = event.get("data", {}).get("new_status")
        if (
            new_status == ActionStatus.PROCESSING
            and action.get("mode") == ExecutionMode.ASYNC
            and action.get("engagement")
        ):
            await self._deliver_response(action["engagement"])

    async def _on_waiting_for_input(self, event: "Event") -> None:
        """Handle waiting event - deliver prompt."""
        prompt = event.get("data", {}).get("prompt")
        if prompt:
            await self._deliver_response(prompt)

    async def _deliver_response(self, response: str) -> None:
        """Deliver response via TTS and data channel."""
        if not response:
            return
        self._logger.info(f"[DELIVER] {response[:100]}...")

        # Send via data channel for cards
        await self._handle_voice_response(response)

        # Synthesize TTS
        if self._session:
            try:
                await self._session.say(response, allow_interruptions=True)
            except Exception as e:
                self._logger.error(f"[DELIVER] TTS failed: {e}")

    async def _process_via_pa(self, transcript: str) -> None:
        """
        Process transcript via Planning Agent.

        Uses superkik backbone if available, otherwise falls back to
        ReActOrc (stub until Task 5 implementation).
        """
        # Try superkik backbone first
        if self._backbone and self._backbone.initialized:
            try:
                self._logger.info(f"[PA] Processing via superkik backbone: {transcript[:50]}...")
                response = await self._backbone.process_input(transcript)
                # Response is handled by event bridge (TTS + data channel)
                # Final response is returned for logging only
                if response:
                    self._logger.debug(f"[PA] Backbone response: {response[:100]}...")
                return
            except Exception as e:
                self._logger.error(f"[PA] Superkik backbone failed: {e}")
                # Fall through to ReActOrc fallback

        # Fallback to ReActOrc (stub - implemented in Task 5)
        if self._react_orc:
            self._logger.debug(f"[PA] Processing via ReActOrc: {transcript[:50]}...")
            # TODO: Implement ReActOrc processing in Task 5
            pass

    def create_agent(self, ctx=None) -> SuperKikAgent:
        """Create SuperKik agent with dynamically registered tools."""
        persona = self.config.get("persona", {})
        persona_name = persona.get("name") if isinstance(persona, dict) else None

        agent_context = build_agent_context(
            agent_name=self.config.get("agent_name") or persona_name or "SuperKik",
            org_name=(
                getattr(self.user_state, "space_name", None)
                or self.config.get("org_name")
            ),
            agent_handle=(
                self.config.get("agent_handle") or self.config.get("pilot_handle")
            ),
            org_id=self.config.get("space_id") or self.config.get("org_id"),
        )

        user_context = build_user_context(
            user_name=getattr(self.user_state, "user_name", None),
            user_location=self.superkik_config.default_location,
            preferred_language=getattr(self.user_state, "language", None),
            preferences=self._user_preferences,
            provider_history=self._provider_history,
            current_booking_state=self._get_active_booking_state(),
        )

        session_context = build_session_state_context(
            current_results=[p.to_dict() for p in self._session_state.current_results],
            selected_provider=(
                self._session_state.selected_provider.to_dict()
                if self._session_state.selected_provider
                else None
            ),
            pending_action=self._session_state.pending_action,
            active_filters=self._session_state.active_filters,
            active_call_id=self._session_state.active_call_id,
        )

        base_instructions = self.prompt_manager._create_assistant_prompt()

        superkik_prompt = get_superkik_prompt(
            config=self.config,
            agent_context=agent_context,
            user_context=user_context,
            session_state=session_context,
            compact=self._get_superkik_config_value("use_compact_prompt", False),
        )

        instructions = f"{base_instructions}\n\n{superkik_prompt}"

        # Note: Callee mode instructions are NOT added here because create_agent()
        # is only called once at session start. Callee mode is activated dynamically
        # during an active call via _switch_to_callee_mode() which uses
        # session.generate_reply(instructions=...) to inject context into the
        # running agent session.

        # Get dynamic tools from registry
        tools = self.get_agent_tools() if self._tool_registry else []

        agent = SuperKikAgent(
            handler=self,
            user_state=self.user_state,
            instructions=instructions,
            tools=tools,
        )

        # Log tool registration
        if tools:
            tool_names = [f.__name__ for f in tools]
            self._logger.info(
                f"SuperKikAgent created with {len(tool_names)} dynamic tools: {tool_names}"
            )
        else:
            self._logger.warning("No dynamic tools registered")

        return agent

    def get_agent_tools(self) -> List[Callable]:
        """
        Get all tool functions for the agent.

        Called by LiveKit agent framework to register tools.

        Returns:
            List of @function_tool decorated functions
        """
        if not self._tool_registry:
            return []
        return self._tool_registry.get_all_tool_functions()

    def _get_active_booking_state(self) -> Optional[str]:
        """Get description of active booking if any."""
        if not self._pending_bookings:
            return None

        for booking_id, status in self._pending_bookings.items():
            if status.status == BookingStatusType.PENDING:
                request = status.request
                if request:
                    return f"Pending: {request.provider_name} @ {request.requested_time_str}"

        return None

    async def execute_with_context(self, ctx: "JobContext") -> Any:
        """Execute SuperKik handler with job context."""
        # Sync room name from actual ctx.room to ensure SIP calls go to correct room
        actual_room_name = ctx.room.name
        if actual_room_name and actual_room_name != self._room_name:
            self._logger.info(
                f"[ROOM_SYNC] Updating room name: {self._room_name} -> {actual_room_name}"
            )
            self._room_name = actual_room_name
            # Update SIP manager's room name to match
            if self._sip_manager:
                self._sip_manager.set_room_name(actual_room_name)
                self._logger.info(
                    f"[SIP_MANAGER] Room name synced to: {actual_room_name}"
                )

        await self._init_superkik_event_bridge(ctx)
        # Set up SIP call status monitoring for real-time updates
        self._setup_sip_call_monitoring(ctx)

        # Identify main user from current remote participants (if already in room)
        try:
            from livekit import rtc

            for identity, participant in ctx.room.remote_participants.items():
                if (
                    identity != ctx.room.local_participant.identity
                    and participant.kind != rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    and self._main_user_participant is None
                ):
                    self._main_user_participant = participant
                    self._logger.info(
                        f"[MAIN_USER] Identified main user at start: {identity}"
                    )
                    break
        except Exception as e:
            self._logger.warning(f"[MAIN_USER] Failed to identify main user: {e}")

        await super().execute_with_context(ctx)

    def _setup_session_events(self, session: "AgentSession") -> None:
        """Set up event handlers for the session."""
        super()._setup_session_events(session)

        # Add SuperKik-specific user input handling for orchestrator, dual-stream, and triggers
        @session.on("user_input_transcribed")
        def on_user_input(event: "UserInputTranscribedEvent"):
            if not event.is_final or not event.transcript:
                return

            transcript = event.transcript

            # Route 1: User mode with SharedContext enabled
            # Routes through two-tier classification (local response vs PA)
            if (
                self._shared_context
                and not self._is_callee_mode
                and not self._is_patch_mode
            ):
                self._logger.debug("[ROUTING] User mode → SharedContext")
                asyncio.create_task(self._route_user_input(transcript))
                return  # Skip native agent handling

            # Route 2: Callee mode - dual stream handling (unchanged)
            # In callee mode, route transcripts through dual-stream handler
            # Audio focus is on SIP participant, so transcripts are from callee
            if self._is_callee_mode and not self._is_patch_mode:
                self._logger.info(
                    f"[DUAL_STREAM] Received callee transcript: {transcript[:50]}..."
                )
                asyncio.create_task(
                    self._handle_dual_stream_transcript("callee", transcript)
                )

                # Also check for patch trigger patterns
                transcript_lower = transcript.lower()
                if any(
                    pattern in transcript_lower for pattern in PATCH_TRIGGER_PATTERNS
                ):
                    self._logger.info(
                        f"[PATCH_TRIGGER] Detected patch command: '{transcript}'"
                    )
                    asyncio.create_task(self._switch_to_patch_mode())

    async def _init_superkik_event_bridge(self, ctx: "JobContext") -> None:
        """Initialize event bridge for SuperKik-specific events."""
        if not self._event_bridge:
            from super.core.voice.livekit.event_bridge import LiveKitEventBridge

            self._event_bridge = LiveKitEventBridge(
                logger=self._logger.getChild("events"),
            )
            await self._event_bridge.initialize(ctx)

    # -------------------------------------------------------------------------
    # Dual-Stream Speaker Diarization
    # -------------------------------------------------------------------------

    async def _add_transcript_to_context(
        self,
        speaker_role: str,
        transcript: str,
    ) -> None:
        """
        Add transcript to chat context with speaker attribution.

        Builds persistent conversation history so the agent can see
        the full dialogue thread with clear speaker labels.

        Args:
            speaker_role: "callee" or "user"
            transcript: The transcribed text
        """
        if not self._agent or not hasattr(self._agent, "chat_ctx"):
            self._logger.debug(
                "[CONTEXT] No agent or chat_ctx available, skipping context update"
            )
            return

        provider_name = (
            self._callee_mode_context.get("provider_name", "Callee")
            if self._callee_mode_context
            else "Callee"
        )
        user_name = (
            self._callee_mode_context.get("user_name", "User")
            if self._callee_mode_context
            else "User"
        )

        # Format message with speaker label
        if speaker_role == "callee":
            content = f"[{provider_name}]: {transcript}"
        else:
            content = f"[{user_name} - background]: {transcript}"

        try:
            chat_ctx = self._agent.chat_ctx.copy()
            chat_ctx.add_message(role="user", content=content)
            await self._agent.update_chat_ctx(chat_ctx)
            self._logger.debug(
                f"[CONTEXT] Added {speaker_role} transcript to chat context"
            )
        except Exception as e:
            self._logger.error(f"[CONTEXT] Failed to update chat context: {e}")

    async def _handle_dual_stream_transcript(
        self,
        speaker_role: str,
        transcript: str,
    ) -> None:
        """
        Handle transcript from dual-stream speaker diarization.

        In callee mode, transcripts are added to persistent chat context.
        The agent responds to callee transcripts but not to user transcripts
        (user transcripts are just context updates for the agent to see).

        Args:
            speaker_role: "callee" or "user"
            transcript: The transcribed text
        """
        # Only process in callee mode, not in patch mode
        if not self._is_callee_mode or self._is_patch_mode:
            return

        # Add transcript to persistent chat context
        await self._add_transcript_to_context(speaker_role, transcript)

        if speaker_role == "callee" and self._session:
            # Callee spoke - save to database with call_ref, then agent responds
            await self._save_callee_message(transcript)

            # Re-check callee mode after await (could have changed during save)
            # This prevents race condition with _switch_to_user_mode
            if not self._is_callee_mode:
                self._logger.info(
                    "[DUAL_STREAM] Callee mode ended during save, skipping reply"
                )
                return

            # Context already has full conversation, just trigger reply
            self._logger.info("[DUAL_STREAM] Triggering agent response to callee")
            await self._session.generate_reply()
        elif speaker_role == "user":
            # User spoke - context updated, but don't force a response
            # Agent will see this when responding to next callee message
            self._logger.debug(
                "[DUAL_STREAM] User context added, no response triggered"
            )

    async def _save_callee_message(self, transcript: str) -> None:
        """
        Save callee (provider) message to database with call reference.

        Args:
            transcript: The callee's transcribed speech
        """
        if not self.user_state or not self.user_state.thread_id:
            return

        try:
            # Increment sequence counter
            self._call_message_seq += 1

            # Get call reference info
            call_id = self._current_call.call_id if self._current_call else None
            provider_name = (
                self._callee_mode_context.get("provider_name", "Callee")
                if self._callee_mode_context
                else "Callee"
            )

            # Create message with enhanced call_ref
            # Use callee user for proper attribution (not self.agent)
            callee_user = self._callee_user or self.agent
            msg = Message.create(
                transcript,
                user=callee_user,
                event=Event.USER_MESSAGE,  # Callee is a "user" in the conversation
                data={
                    "block_type": "callee_msg",
                    "type": "voice_call_transcript",
                    "call_ref": {
                        "call_id": call_id,
                        "provider_name": provider_name,
                        "speaker": "callee",
                        "call_seq": self._call_message_seq,
                        "timestamp_ms": int(time.time() * 1000),
                    },
                },
            )

            self._send_callback(msg, thread_id=str(self.user_state.thread_id))
            self._logger.info(
                f"[CALLEE_MSG] Saved callee message: "
                f"call_id={call_id}, seq={self._call_message_seq}, len={len(transcript)}"
            )

        except Exception as e:
            self._logger.error(f"[CALLEE_MSG] Failed to save callee message: {e}")

    async def _save_agent_call_message(self, transcript: str) -> None:
        """
        Save agent's response during a call to database with call reference.

        Args:
            transcript: The agent's spoken response
        """
        if not self.user_state or not self.user_state.thread_id:
            return

        # Only save if we're in an active call
        if not self._current_call or not self._is_callee_mode:
            return

        try:
            # Increment sequence counter
            self._call_message_seq += 1

            call_id = self._current_call.call_id
            provider_name = (
                self._callee_mode_context.get("provider_name", "Unknown")
                if self._callee_mode_context
                else "Unknown"
            )

            msg = Message.create(
                transcript,
                user=self.agent,
                event=Event.AGENT_MESSAGE,
                data={
                    "block_type": "callee_msg",
                    "type": "voice_call_transcript",
                    "call_ref": {
                        "call_id": call_id,
                        "provider_name": provider_name,
                        "speaker": "agent",
                        "call_seq": self._call_message_seq,
                        "timestamp_ms": int(time.time() * 1000),
                    },
                },
            )

            self._send_callback(msg, thread_id=str(self.user_state.thread_id))
            self._logger.info(
                f"[AGENT_CALL_MSG] Saved agent call message: "
                f"call_id={call_id}, seq={self._call_message_seq}, len={len(transcript)}"
            )

        except Exception as e:
            self._logger.error(f"[AGENT_CALL_MSG] Failed to save agent call message: {e}")

    # -------------------------------------------------------------------------
    # Session State Management
    # -------------------------------------------------------------------------

    def update_search_results(self, result: SearchResult) -> None:
        """Update session state with new search results."""
        self._last_search_result = result
        self._session_state.current_results = result.providers
        self._session_state.selected_provider = None
        self._session_state.pending_action = None
        self._session_state.turn_count += 1

    def select_provider(self, provider: ProviderCard) -> None:
        """Select a provider from current results."""
        self._session_state.selected_provider = provider

        if self._user_preferences:
            self._user_preferences.set_last_provider(provider.id, provider.name)
            self._provider_history.append(
                {
                    "name": provider.name,
                    "id": provider.id,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

    def set_pending_call(self, provider: ProviderCard) -> None:
        """Set pending call action for confirmation."""
        self._session_state.set_pending_action(
            "call",
            {
                "provider_id": provider.id,
                "provider_name": provider.name,
                "provider_phone": provider.phone,
            },
        )

    def set_pending_booking(
        self,
        provider: ProviderCard,
        time_slot: Optional[str] = None,
        service: Optional[str] = None,
    ) -> None:
        """Set pending booking action for confirmation."""
        self._session_state.set_pending_action(
            "booking",
            {
                "provider_id": provider.id,
                "provider_name": provider.name,
                "time_slot": time_slot,
                "service": service,
            },
        )

    def apply_filter(self, filter_type: str, value: Any) -> None:
        """Apply a search filter."""
        self._session_state.active_filters[filter_type] = value

        if self._user_preferences:
            filter_key = f"filter_{filter_type}"
            count = self._user_preferences.filters.get(f"{filter_key}_count", 0)
            self._user_preferences.filters[f"{filter_key}_count"] = count + 1

            if count + 1 >= 3:
                self._user_preferences.filters[filter_type] = value
                self._logger.info(f"Auto-saved preference: {filter_type}={value}")

    def clear_filters(self) -> None:
        """Clear all active filters."""
        self._session_state.active_filters = {}

    def get_provider_by_rank(self, rank: int) -> Optional[ProviderCard]:
        """Get provider from current results by rank (1-indexed)."""
        if not self._session_state.current_results:
            return None

        index = rank - 1
        if 0 <= index < len(self._session_state.current_results):
            return self._session_state.current_results[index]

        return None

    def get_last_provider(self) -> Optional[Dict[str, Any]]:
        """Get last used provider from history."""
        if not self._provider_history:
            return None
        return self._provider_history[-1]

    # -------------------------------------------------------------------------
    # Intent-Aware Response Helpers
    # -------------------------------------------------------------------------

    def classify_user_intent(self, text: str) -> str:
        """Classify user intent from utterance."""
        intent = classify_intent(text)
        self._session_state.last_intent = intent
        return intent

    def format_search_response(self, provider: ProviderCard) -> str:
        """Format a voice-optimized search result response."""
        open_status = "open now" if provider.is_open else "closed"
        distance = (
            f"{provider.distance_km:.1f}km" if provider.distance_km > 0 else "nearby"
        )

        return format_voice_response(
            "search_found",
            name=provider.name,
            rating=provider.rating,
            distance=distance,
            open_status=open_status,
        )

    def format_call_response(self, status: CallStatusType, provider_name: str) -> str:
        """Format call status response."""
        if status == CallStatusType.CONNECTING:
            return format_voice_response("call_connecting", name=provider_name)
        elif status == CallStatusType.RINGING:
            return format_voice_response("call_ringing")
        elif status == CallStatusType.ACTIVE:
            return format_voice_response("call_connected")
        elif status == CallStatusType.FAILED:
            return format_voice_response("call_failed")
        elif status == CallStatusType.ENDED:
            return format_voice_response("call_ended", duration="")
        return ""

    # -------------------------------------------------------------------------
    # Response Override for Card Integration
    # -------------------------------------------------------------------------

    async def _handle_voice_response(self, content: str) -> None:
        """
        Override parent method to use pending message_id for correlation.

        In VOICE mode, when the assistant responds after tool execution,
        this ensures the response uses the same message_id as the cards
        (which were sent immediately) for proper frontend correlation.

        Args:
            content: The assistant's response text
        """
        # Use pending message_id if available (correlates with already-sent cards)
        message_id = self._pending_message_id or str(uuid.uuid4())[:12]
        self._logger.info(
            f"[VOICE_RESPONSE] Sending text response "
            f"(id={message_id}, has_pending_id={self._pending_message_id is not None})"
        )

        # Handle callee mode separately (different save path)
        if self._is_callee_mode and self._current_call:
            await self._save_agent_call_message(content)

        # Send text-only response via data channel
        # Parent's _send_data_response handles: transcript storage, DB save, publishing
        try:
            await self._send_data_response(content, None, message_id)
            self._logger.debug(
                f"[VOICE_MODE] Sent text response via {TOPIC_LK_CHAT} (id={message_id})"
            )
        except Exception as e:
            self._logger.warning(f"[VOICE_MODE] Failed to send text response: {e}")

        # Signal first response sent
        if not self._first_response_sent.is_set():
            self._first_response_sent.set()

        # Notify plugins
        await self.plugins.broadcast_event("on_agent_speech", content)

    async def _send_data_response(
        self,
        response_text: str,
        block_data: dict | None = None,
        message_id: str | None = None,
        cards: Dict[str, Any] | None = None,
    ) -> None:
        """
        Send text-only response with message_id correlation.

        Cards are sent immediately when received via _publish_* methods.
        This method sends just the text response with the same message_id
        so the frontend can correlate text with previously sent cards.

        Args:
            response_text: Full response text
            block_data: Original block data for context
            message_id: Unique ID for correlating with streaming chunks
            cards: Ignored - cards are sent immediately by _publish_* methods
        """
        # Use pending message_id for correlation with previously sent cards
        effective_message_id = message_id or self._pending_message_id

        self._logger.debug(
            f"[TEXT_RESPONSE] Sending text-only response "
            f"(id={effective_message_id}): {response_text[:100]}..."
        )

        # Call parent implementation without cards (cards already sent)
        await super()._send_data_response(
            response_text=response_text,
            block_data=block_data,
            message_id=effective_message_id,
            cards=None,  # Cards already sent immediately
        )

        self._logger.info(
            f"[TEXT_SENT] Response sent (id={effective_message_id}): "
            f"{response_text[:100]}..."
        )

        # Clear pending message_id after use
        self._pending_message_id = None

    def _save_card_to_db(
        self,
        card_data: Dict[str, Any],
        message_id: str,
    ) -> None:
        """
        Save card data to database for persistence across page reloads.

        Creates a card-only message block that will be loaded when conversation
        history is fetched.

        Args:
            card_data: Card data dict with type, items, count, etc.
            message_id: Message ID for correlation
        """
        thread_id = str(self.user_state.thread_id) if self.user_state.thread_id else None
        if not thread_id:
            self._logger.warning("[CARDS_DB] No thread_id available, skipping DB save")
            return

        try:
            # Create message with cards data for database persistence
            msg = Message.create(
                "",  # Empty content for card-only block
                user=self.agent,
                event=Event.AGENT_MESSAGE,
                data={"cards": card_data, "block_type": "cards"},
            )

            # Save via callback (triggers save_message_block)
            self._send_callback(msg, thread_id=thread_id)

            self._logger.info(
                f"[CARDS_DB] Saved {card_data.get('type')} card to DB "
                f"(id={message_id}, count={card_data.get('count', 0)})"
            )
        except Exception as e:
            self._logger.error(f"[CARDS_DB] Failed to save card to DB: {e}")

    # -------------------------------------------------------------------------
    # SuperKik Event Publishing Methods
    # -------------------------------------------------------------------------

    async def _publish_provider_cards(
        self,
        providers: List[ProviderCard],
        query: Optional[str] = None,
        message_id: Optional[str] = None,
    ) -> bool:
        """
        Publish provider cards immediately to frontend via lk.chat topic.

        Cards are sent with proper block_response format for immediate UI rendering.
        Also saves cards to database for persistence across page reloads.
        Stores message_id for correlation with subsequent LLM text response.

        Args:
            providers: List of provider cards
            query: Optional search query
            message_id: Optional message_id for correlation
        """
        if not self._event_bridge:
            self._logger.warning("Event bridge not available for provider cards")
            return False

        try:
            effective_message_id = message_id or str(uuid.uuid4())[:12]

            card_data = {
                "type": "provider",
                "items": [p.to_dict() for p in providers],
                "count": len(providers),
                "query": query,
                "message_id": effective_message_id,
            }

            # Build proper block_response format (card-only, no text)
            block = self._build_response_block(
                response_text="",
                cards=card_data,
                message_id=effective_message_id,
            )

            # Publish immediately to lk.chat with proper format
            result = await self._event_bridge.publish_data(
                data=block,
                topic=TOPIC_LK_CHAT,
                reliable=True,
            )

            if result:
                self._logger.info(
                    f"[CARDS_SENT] Published {len(providers)} provider cards "
                    f"to '{TOPIC_LK_CHAT}' (id={effective_message_id})"
                )
                # Store message_id for correlation with upcoming LLM response
                self._pending_message_id = effective_message_id

                # Save cards to database for persistence
                self._save_card_to_db(card_data, effective_message_id)
            else:
                self._logger.warning(
                    f"[CARDS_FAILED] Failed to publish provider cards to '{TOPIC_LK_CHAT}'"
                )

            return result

        except Exception as e:
            self._logger.error(f"Failed to publish provider cards: {e}")
            return False

    async def _publish_call_status(
        self,
        call_status: CallStatus,
        message_id: Optional[str] = None,
    ) -> bool:
        """
        Publish call status update immediately to frontend via lk.chat topic.

        Uses call_id as block_id for consistent card updates across status changes.
        This ensures ringing → active → ended all update the same UI card.
        """
        if not self._event_bridge:
            return False

        try:
            if call_status.status in (
                CallStatusType.ACTIVE,
                CallStatusType.CONNECTING,
                CallStatusType.RINGING,
            ):
                self._session_state.active_call_id = call_status.call_id
            elif call_status.status in (CallStatusType.ENDED, CallStatusType.FAILED):
                self._session_state.active_call_id = None

            # Use call_id as message_id for consistent card updates
            effective_message_id = message_id or f"call_{call_status.call_id}"

            card_data = {
                "type": "call",
                "items": [call_status.to_dict()],
                "message_id": effective_message_id,
                "block_id": f"call_{call_status.call_id}",
            }

            # Build proper block_response format
            block = self._build_response_block(
                response_text="",
                cards=card_data,
                message_id=effective_message_id,
            )

            self._logger.debug(
                f"[CALL_STATUS] Publishing status={call_status.status.value} "
                f"block_id=call_{call_status.call_id}"
            )

            # Save call block to database
            if self.user_state and self.user_state.thread_id:
                msg = Message.create(
                    f"Call {call_status.status.value}: {call_status.provider_name}",
                    user=self.agent,
                    event=Event.AGENT_MESSAGE,
                    data={
                        "block_type": "call",
                        "call": call_status.to_dict(),
                    },
                )
                self._send_callback(msg, thread_id=str(self.user_state.thread_id))
                self._logger.info(
                    f"[CALL_STATUS] Saved call block: status={call_status.status.value}, "
                    f"call_id={call_status.call_id}"
                )

            result = await self._event_bridge.publish_data(
                data=block,
                topic=TOPIC_LK_CHAT,
                reliable=True,
            )

            if result:
                self._pending_message_id = effective_message_id

            return result

        except Exception as e:
            self._logger.error(f"Failed to publish call status: {e}")
            return False

    async def _publish_booking_update(
        self,
        booking_status: BookingStatus,
        message_id: Optional[str] = None,
    ) -> bool:
        """
        Publish booking update immediately to frontend via lk.chat topic.
        """
        if not self._event_bridge:
            return False

        try:
            if booking_status.status == BookingStatusType.PENDING:
                self._session_state.active_booking_id = booking_status.booking_id
            elif booking_status.status in (
                BookingStatusType.CONFIRMED,
                BookingStatusType.CANCELLED,
            ):
                self._session_state.active_booking_id = None

            effective_message_id = message_id or str(uuid.uuid4())[:12]

            card_data = {
                "type": "booking",
                "items": [booking_status.to_dict()],
                "message_id": effective_message_id,
            }

            block = self._build_response_block(
                response_text="",
                cards=card_data,
                message_id=effective_message_id,
            )

            result = await self._event_bridge.publish_data(
                data=block,
                topic=TOPIC_LK_CHAT,
                reliable=True,
            )

            if result:
                self._pending_message_id = effective_message_id
                # Save booking card to database
                self._save_card_to_db(card_data, effective_message_id)

            return result

        except Exception as e:
            self._logger.error(f"Failed to publish booking update: {e}")
            return False

    async def _publish_preferences_update(self) -> bool:
        """Publish user preferences to frontend."""
        if not self._event_bridge or not self._user_preferences:
            return False

        try:
            return await self._event_bridge.publish_data(
                data=self._user_preferences.to_dict(),
                topic=TOPIC_PREFERENCES,
                reliable=True,
            )

        except Exception as e:
            self._logger.error(f"Failed to publish preferences: {e}")
            return False

    async def _publish_session_state(self) -> bool:
        """Publish session state to frontend."""
        if not self._event_bridge:
            return False

        try:
            return await self._event_bridge.publish_data(
                data=self._session_state.to_dict(),
                topic=TOPIC_SESSION_STATE,
                reliable=True,
            )

        except Exception as e:
            self._logger.error(f"Failed to publish session state: {e}")
            return False

    async def _publish_web_results(
        self,
        results: List[WebResultCard],
        query: str,
        message_id: Optional[str] = None,
    ) -> bool:
        """
        Publish web search results immediately to frontend via lk.chat topic.
        """
        if not self._event_bridge:
            self._logger.warning("Event bridge not available for web results")
            return False

        try:
            effective_message_id = message_id or str(uuid.uuid4())[:12]

            card_data = {
                "type": "web",
                "items": [r.to_dict() for r in results],
                "count": len(results),
                "query": query,
                "message_id": effective_message_id,
            }

            block = self._build_response_block(
                response_text="",
                cards=card_data,
                message_id=effective_message_id,
            )

            result = await self._event_bridge.publish_data(
                data=block,
                topic=TOPIC_LK_CHAT,
                reliable=True,
            )

            if result:
                self._pending_message_id = effective_message_id
                # Save web results card to database
                self._save_card_to_db(card_data, effective_message_id)

            return result

        except Exception as e:
            self._logger.error(f"Failed to publish web results: {e}")
            return False

    async def _publish_people_results(
        self,
        people: List[PersonCard],
        query: str,
        message_id: Optional[str] = None,
    ) -> bool:
        """
        Publish people search results immediately to frontend via lk.chat topic.
        """
        if not self._event_bridge:
            self._logger.warning("Event bridge not available for people results")
            return False

        try:
            effective_message_id = message_id or str(uuid.uuid4())[:12]

            card_data = {
                "type": "person",
                "items": [p.to_dict() for p in people],
                "count": len(people),
                "query": query,
                "message_id": effective_message_id,
            }

            block = self._build_response_block(
                response_text="",
                cards=card_data,
                message_id=effective_message_id,
            )

            result = await self._event_bridge.publish_data(
                data=block,
                topic=TOPIC_LK_CHAT,
                reliable=True,
            )

            if result:
                self._pending_message_id = effective_message_id
                # Save people results card to database
                self._save_card_to_db(card_data, effective_message_id)

            return result

        except Exception as e:
            self._logger.error(f"Failed to publish people results: {e}")
            return False

    async def _publish_event_cards(
        self,
        events: List[EventCard],
        query: str,
        message_id: Optional[str] = None,
    ) -> bool:
        """
        Publish event cards immediately to frontend via lk.chat topic.
        """
        if not self._event_bridge:
            self._logger.warning("Event bridge not available for event cards")
            return False

        try:
            effective_message_id = message_id or str(uuid.uuid4())[:12]

            card_data = {
                "type": "event",
                "items": [e.to_dict() for e in events],
                "count": len(events),
                "query": query,
                "message_id": effective_message_id,
            }

            block = self._build_response_block(
                response_text="",
                cards=card_data,
                message_id=effective_message_id,
            )

            result = await self._event_bridge.publish_data(
                data=block,
                topic=TOPIC_LK_CHAT,
                reliable=True,
            )

            if result:
                self._pending_message_id = effective_message_id
                # Save event cards to database
                self._save_card_to_db(card_data, effective_message_id)

            return result

        except Exception as e:
            self._logger.error(f"Failed to publish event cards: {e}")
            return False

    # -------------------------------------------------------------------------
    # SIP Call Status Monitoring & Mode Switching
    # -------------------------------------------------------------------------

    def _setup_sip_call_monitoring(self, ctx: "JobContext") -> None:
        """
        Set up monitoring for SIP participant call status changes.

        Monitors `sip.callStatus` attribute changes on SIP participants to:
        1. Push real-time status updates to the UI
        2. Switch agent mode when call connects (user mode -> callee mode)
        """
        try:
            from livekit import rtc

            @ctx.room.on("participant_attributes_changed")
            def on_participant_attributes_changed(
                changed_attributes: dict,
                participant: rtc.Participant,
            ):
                """Handle SIP participant attribute changes for call status."""
                # Only process SIP participants
                if participant.kind != rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
                    return

                # Check for sip.callStatus changes
                if "sip.callStatus" in changed_attributes:
                    sip_status = changed_attributes["sip.callStatus"]
                    self._logger.info(
                        f"[SIP_STATUS] Participant {participant.identity} "
                        f"call status changed to: {sip_status}"
                    )

                    # Handle the status change asynchronously
                    import asyncio

                    asyncio.create_task(
                        self._handle_sip_call_status_change(
                            sip_status, participant.identity
                        )
                    )

            @ctx.room.on("participant_connected")
            def on_sip_participant_connected(participant: rtc.Participant):
                """Handle SIP participant connecting (call answered)."""
                if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
                    self._logger.info(
                        f"[SIP_CONNECTED] SIP participant connected: {participant.identity}"
                    )
                    # Store SIP participant reference for audio routing
                    self._sip_participant = participant
                    # Log participant details for debugging audio routing
                    self._logger.info(
                        f"[SIP_CONNECTED] Tracks: audio_tracks={len(list(participant.track_publications.values()))}, "
                        f"room={ctx.room.name}"
                    )
                    import asyncio

                    asyncio.create_task(
                        self._handle_sip_participant_connected(participant)
                    )
                else:
                    # Track main user participant (first non-SIP, non-agent participant)
                    if (
                        self._main_user_participant is None
                        and participant.identity != ctx.room.local_participant.identity
                    ):
                        self._main_user_participant = participant
                        self._logger.info(
                            f"[MAIN_USER] Identified main user: {participant.identity}"
                        )

            @ctx.room.on("track_subscribed")
            def on_track_subscribed(
                track: rtc.Track,
                publication: rtc.TrackPublication,
                participant: rtc.Participant,
            ):
                """Handle track subscription - important for SIP audio routing."""
                if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
                    self._logger.info(
                        f"[SIP_TRACK] Track subscribed from SIP participant: "
                        f"identity={participant.identity}, track_kind={track.kind}, "
                        f"track_sid={track.sid}"
                    )

            @ctx.room.on("participant_disconnected")
            def on_sip_participant_disconnected(participant: rtc.Participant):
                """Handle SIP participant disconnecting (call ended)."""
                if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
                    self._logger.info(
                        f"[SIP_DISCONNECTED] SIP participant disconnected: {participant.identity}"
                    )
                    import asyncio

                    asyncio.create_task(
                        self._handle_sip_participant_disconnected(participant.identity)
                    )

            self._logger.info("[SIP_MONITOR] SIP call status monitoring set up")

        except ImportError:
            self._logger.warning("livekit.rtc not available for SIP monitoring")
        except Exception as e:
            self._logger.error(f"Failed to set up SIP monitoring: {e}")

    async def _handle_sip_call_status_change(
        self,
        sip_status: str,
        _participant_identity: str,
    ) -> None:
        """
        Handle SIP call status changes and push updates to UI.

        SIP status values:
        - "dialing": Call is being dialed
        - "ringing": Remote party is ringing
        - "active": Call is connected and active
        - "hangup": Call has ended

        Args:
            sip_status: SIP call status string
            participant_identity: Identity of the SIP participant (phone number)
        """
        if not self._current_call:
            self._logger.debug(
                f"No current call tracked, ignoring SIP status: {sip_status}"
            )
            return

        # Guard: Skip if we already processed this exact status (prevents duplicate events)
        if self._last_processed_sip_status == sip_status:
            self._logger.debug(f"[SIP_STATUS] Skipping duplicate status: {sip_status}")
            return

        # Update last processed status
        self._last_processed_sip_status = sip_status

        # Map SIP status to CallStatusType
        status_map = {
            "dialing": CallStatusType.CONNECTING,
            "ringing": CallStatusType.RINGING,
            "active": CallStatusType.ACTIVE,
            "hangup": CallStatusType.ENDED,
        }

        new_status = status_map.get(sip_status)
        if not new_status:
            self._logger.warning(f"Unknown SIP status: {sip_status}")
            return

        # Update call status
        old_status = self._current_call.status

        # Skip if status hasn't actually changed
        if old_status == new_status:
            self._logger.debug(
                f"[SIP_STATUS] Status unchanged: {new_status.value}, skipping"
            )
            return

        self._current_call.status = new_status

        self._logger.info(
            f"[CALL_STATUS_UPDATE] {old_status.value} -> {new_status.value} "
            f"for {self._current_call.provider_name}"
        )

        # Handle call ended
        if new_status == CallStatusType.ENDED:
            self._current_call.ended_at = datetime.utcnow().isoformat()
            # Calculate duration
            if self._current_call.started_at:
                try:
                    start = datetime.fromisoformat(self._current_call.started_at)
                    duration = (datetime.utcnow() - start).total_seconds()
                    self._current_call.duration_seconds = int(duration)
                except (ValueError, TypeError):
                    pass

        # Push status update to UI
        if self._event_bridge:
            await self._publish_call_status(self._current_call)
            self._logger.info(f"[UI_UPDATE] Published call status: {new_status.value}")

        # Handle mode switching when call becomes active (with guard)
        if new_status == CallStatusType.ACTIVE and old_status != CallStatusType.ACTIVE:
            await self._switch_to_callee_mode()

        # Clean up when call ends
        if new_status == CallStatusType.ENDED:
            await self._switch_to_user_mode()

    async def _handle_sip_participant_connected(
        self,
        participant: Any,  # rtc.Participant object
    ) -> None:
        """Handle SIP participant connected (call answered)."""

        if not self._current_call:
            return

        # Guard: Skip if already in ACTIVE state (already handled by attribute change)
        if self._current_call.status == CallStatusType.ACTIVE:
            self._logger.debug(
                "[SIP_CONNECTED] Already in ACTIVE state, skipping duplicate"
            )
            return

        # Guard: Skip if already in callee mode (prevents duplicate mode switch)
        if self._is_callee_mode:
            self._logger.debug(
                "[SIP_CONNECTED] Already in callee mode, skipping mode switch"
            )
            return

        self._current_call.status = CallStatusType.ACTIVE

        self._logger.info(
            f"[CALL_CONNECTED] Call with {self._current_call.provider_name} "
            f"is now connected"
        )

        # Push status update
        if self._event_bridge:
            await self._publish_call_status(self._current_call)

        # Switch to callee mode
        await self._switch_to_callee_mode()

    async def _handle_sip_participant_disconnected(
        self,
        _participant_identity: str,
    ) -> None:
        """Handle SIP participant disconnected (call ended)."""
        if not self._current_call:
            return

        # Guard: Skip if already in ENDED state (already handled by attribute change)
        if self._current_call.status == CallStatusType.ENDED:
            self._logger.debug(
                "[SIP_DISCONNECTED] Already in ENDED state, skipping duplicate"
            )
            return

        # Update status to ENDED
        self._current_call.status = CallStatusType.ENDED
        self._current_call.ended_at = datetime.utcnow().isoformat()

        # Calculate duration
        if self._current_call.started_at:
            try:
                start = datetime.fromisoformat(self._current_call.started_at)
                duration = (datetime.utcnow() - start).total_seconds()
                self._current_call.duration_seconds = int(duration)
            except (ValueError, TypeError):
                pass

        self._logger.info(
            f"[CALL_ENDED] Call with {self._current_call.provider_name} ended "
            f"(duration: {self._current_call.duration_seconds}s)"
        )

        # Push status update
        if self._event_bridge:
            await self._publish_call_status(self._current_call)

        # Switch back to user mode
        await self._switch_to_user_mode()

        # Clear current call and reset status tracking
        self._current_call = None
        self._last_processed_sip_status = None

    async def _switch_to_callee_mode(self) -> None:
        """
        Switch agent to callee mode for talking to the third-party (provider).

        In callee mode, the agent:
        1. Changes its persona to speak on behalf of the user
        2. Has instructions to complete the user's objective (booking, inquiry, etc.)
        3. Speaks to the callee (provider) to achieve the goal

        This method:
        1. Builds comprehensive system prompt via _build_callee_system_prompt
        2. Injects persistent system message into chat context (for all future turns)
        3. Generates initial greeting via generate_reply() WITHOUT instructions
           (context-driven approach)
        """
        if not self._current_call:
            return

        # Guard: Prevent duplicate/re-entrant mode switches
        if self._is_callee_mode:
            self._logger.debug("[MODE_SWITCH] Already in callee mode, skipping")
            return

        if self._mode_switch_in_progress:
            self._logger.debug(
                "[MODE_SWITCH] Mode switch already in progress, skipping"
            )
            return

        self._mode_switch_in_progress = True

        try:
            provider_name = self._current_call.provider_name or "the provider"
            user_name = getattr(self.user_state, "user_name", "the user")

            # Build callee-mode context from session state
            objective = self._get_call_objective()

            self._logger.info(
                f"[MODE_SWITCH] Switching to CALLEE mode for call with {provider_name}"
            )
            self._logger.info(f"[MODE_SWITCH] Objective: {objective}")

            # Step 0: Switch agent's audio input focus to SIP participant
            if self._session and self._sip_participant:
                try:
                    if hasattr(self._session, "room_io") and self._session.room_io:
                        self._logger.info(
                            f"[MODE_SWITCH] Switching audio focus to SIP participant: "
                            f"{self._sip_participant.identity}"
                        )
                        self._session.room_io.set_participant(self._sip_participant)
                        self._logger.info(
                            "[MODE_SWITCH] Agent audio input now focused on SIP callee"
                        )
                except Exception as e:
                    self._logger.error(
                        f"[MODE_SWITCH] Failed to switch audio focus: {e}"
                    )

            # Step 1: Build comprehensive system prompt and update chat context
            system_prompt = self._build_callee_system_prompt(
                provider_name, user_name, objective
            )

            if self._agent and hasattr(self._agent, "chat_ctx"):
                chat_ctx = self._agent.chat_ctx.copy()
                chat_ctx.add_message(role="system", content=system_prompt)
                await self._agent.update_chat_ctx(chat_ctx)
                self._logger.info(
                    "[MODE_SWITCH] Callee system prompt added to chat context"
                )

            # Step 2: Store mode state (ONLY after context update success)
            self._is_callee_mode = True
            self._callee_mode_context = {
                "provider_name": provider_name,
                "user_name": user_name,
                "objective": objective,
                "started_at": datetime.utcnow().isoformat(),
            }

            # Step 2.5: Create callee user for message attribution
            call_id = self._current_call.call_id if self._current_call else "unknown"
            self._callee_user = User.add_user(
                name=provider_name,
                role=Role.USER,  # Callee is a "user" in the conversation
                _id=f"callee_{call_id}",
                data={
                    "type": "callee",
                    "call_id": call_id,
                    "provider_name": provider_name,
                },
            )
            self._logger.info(
                f"[MODE_SWITCH] Created callee user: {provider_name} (call_id={call_id})"
            )

            # Step 3: Interrupt any ongoing speech and generate initial greeting
            if self._session:
                try:
                    # Interrupt ongoing speech to stop "connecting" message
                    self._logger.info(
                        "[MODE_SWITCH] Interrupting speech before callee greeting"
                    )
                    await self._session.interrupt()

                    self._logger.info(
                        "[MODE_SWITCH] Generating initial callee greeting"
                    )
                    await self._session.generate_reply()  # No instructions!
                    self._logger.info("[MODE_SWITCH] Initial callee greeting generated")
                except Exception as e:
                    self._logger.error(
                        f"[MODE_SWITCH] Failed to generate initial greeting: {e}"
                    )

            # Emit mode switch event
            if self._event_bridge:
                await self._event_bridge.emit_event(
                    "mode_switch",
                    {
                        "mode": "callee",
                        "provider_name": provider_name,
                        "objective": objective,
                    },
                )
        finally:
            self._mode_switch_in_progress = False

    async def _switch_to_patch_mode(self) -> None:
        """
        Switch to patch mode where agent is muted and user talks directly to provider.

        In patch mode:
        1. Agent stops generating speech
        2. Audio is bridged between User and Provider
        3. Agent only monitors for "hang up" or "end call" commands
        """
        if not self._current_call or not self._sip_participant:
            return

        self._is_patch_mode = True
        self._logger.info("[MODE_SWITCH] Entering PATCH mode - Agent muted")

        # Inject patch mode instructions
        if self._agent and hasattr(self._agent, "chat_ctx"):
            try:
                chat_ctx = self._agent.chat_ctx.copy()
                chat_ctx.add_message(
                    role="system",
                    content="""
[PATCH MODE ACTIVE]
The user is now speaking DIRECTLY to the provider. You are now MUTED.
DO NOT generate any speech or use any tools unless the user says:
- "hang up", "end call", "disconnect" -> trigger end_call
- "help", "assistant" -> offer brief help then return to silence
Stay silent and let them talk.
""",
                )
                await self._agent.update_chat_ctx(chat_ctx)
                self._logger.info("[MODE_SWITCH] Patch mode instructions added to chat")
            except Exception as e:
                self._logger.error(
                    f"[MODE_SWITCH] Failed to update chat context for patch mode: {e}"
                )

        # Notify UI
        if self._event_bridge:
            await self._event_bridge.emit_event(
                "mode_switch",
                {
                    "mode": "patch",
                    "provider_name": self._current_call.provider_name,
                    "message": "You're now connected directly. Say 'end call' when done.",
                },
            )

    async def _switch_to_user_mode(self) -> None:
        """
        Switch agent back to user mode after call ends.

        In user mode, the agent speaks directly to the user.
        This method:
        1. Injects a system message to mark callee mode as ended
        2. Generates transition reply to summarize the call to the user
        """
        # Guard: Prevent duplicate/re-entrant mode switches
        if not self._is_callee_mode:
            self._logger.debug("[MODE_SWITCH] Already in user mode, skipping")
            return

        if self._mode_switch_in_progress:
            self._logger.debug(
                "[MODE_SWITCH] Mode switch already in progress, skipping"
            )
            return

        self._mode_switch_in_progress = True

        try:
            self._logger.info("[MODE_SWITCH] Switching back to USER mode")

            # Build transition context for informing user about call outcome
            call_summary = self._build_call_summary()
            user_name = getattr(self.user_state, "user_name", "the user")

            self._is_callee_mode = False
            self._callee_mode_context = None
            self._callee_user = None  # Clear callee user representation

            # Step 0: Switch agent's audio input focus back to main user
            # This ensures the agent listens to the user again, not the (disconnected) SIP participant
            if self._session and self._main_user_participant:
                try:
                    if hasattr(self._session, "room_io") and self._session.room_io:
                        self._logger.info(
                            f"[MODE_SWITCH] Switching audio focus back to main user: "
                            f"{self._main_user_participant.identity}"
                        )
                        self._session.room_io.set_participant(
                            self._main_user_participant
                        )
                        self._logger.info(
                            "[MODE_SWITCH] Agent audio input now focused on main user"
                        )
                except Exception as e:
                    self._logger.error(
                        f"[MODE_SWITCH] Failed to switch audio focus to main user: {e}"
                    )
            elif self._session and not self._main_user_participant:
                self._logger.warning(
                    "[MODE_SWITCH] Cannot switch audio - main user not tracked"
                )

            # Clear SIP participant reference
            self._sip_participant = None

            # Step 1: Inject system message to mark callee mode as ended
            # This updates the persistent context for all future turns
            if self._agent and hasattr(self._agent, "chat_ctx"):
                try:
                    chat_ctx = self._agent.chat_ctx.copy()
                    chat_ctx.add_message(
                        role="system",
                        content=f"\n[CALLEE MODE ENDED]\nThe third-party call has ended. {call_summary}\nYou are now speaking directly to {user_name} again. Summarize the call outcome.",
                    )
                    await self._agent.update_chat_ctx(chat_ctx)
                    self._logger.info("[MODE_SWITCH] User mode context added to chat")
                except Exception as e:
                    self._logger.error(
                        f"[MODE_SWITCH] Failed to update chat context: {e}"
                    )

            # Step 2: Interrupt any ongoing response and generate transition reply
            if self._session and call_summary:
                try:
                    # Interrupt any ongoing callee response first
                    self._logger.info(
                        "[MODE_SWITCH] Interrupting any ongoing response before summary"
                    )
                    await self._session.interrupt()

                    transition_prompt = self._build_user_mode_transition_prompt(
                        call_summary
                    )
                    self._logger.info("[MODE_SWITCH] Generating call summary for user")
                    await self._session.generate_reply(instructions=transition_prompt)
                    self._logger.info(
                        "[MODE_SWITCH] Successfully transitioned back to user mode"
                    )
                except Exception as e:
                    self._logger.error(
                        f"[MODE_SWITCH] Failed to generate transition reply: {e}"
                    )

            # Emit mode switch event
            if self._event_bridge:
                await self._event_bridge.emit_event(
                    "mode_switch",
                    {"mode": "user"},
                )
        finally:
            self._mode_switch_in_progress = False

    def _get_call_objective(self) -> str:
        """
        Get the objective for the current call based on session state.

        Returns a description of what the agent should accomplish.
        """
        # Use structured CallContext if available
        if self._current_call_context:
            return self._current_call_context.build_instruction_set()

        # Fallback to pending action
        pending = self._session_state.pending_action
        if pending:
            action_type = pending.get("type", "")
            params = pending.get("params", {})

            if action_type == "booking":
                time_slot = params.get("time_slot", "")
                service = params.get("service", "")
                if time_slot:
                    return f"Make a booking for {time_slot}" + (
                        f" for {service}" if service else ""
                    )
                return "Make a booking/appointment"

            if action_type == "inquiry":
                return params.get("question", "Get information about services")

        # Check for booking in progress
        if self._pending_bookings:
            for booking in self._pending_bookings.values():
                if booking.status == BookingStatusType.PENDING:
                    request = booking.request
                    if request:
                        return f"Confirm booking for {request.requested_time_str or 'today'}"

        # Default objective
        return "Inquire about availability and services"

    def _build_callee_mode_prompt(
        self,
        provider_name: str,
        user_name: str,
        objective: str,
    ) -> str:
        """
        Build the callee mode prompt for injection into the agent session.
        """
        return f"""The call with {provider_name} is now connected. You are now speaking directly to someone at {provider_name}.

IMPORTANT MODE SWITCH: You are no longer speaking to {user_name}. You are now speaking to {provider_name} on behalf of {user_name}.

Your objective:
{objective}

Instructions:
1. Greet the person who answered professionally
2. Introduce yourself as calling on behalf of {user_name}
3. State your purpose clearly based on the goal above
4. Listen to their responses and handle any questions
5. Confirm all details (especially appointment times) before ending
6. Thank them when complete

Language Adaptation:
- If the callee speaks Hindi, you MUST adapt and respond in Hindi (formal 'aap').
- Use proper transliteration if you are using Hindi.

Communication style:
- Be polite and professional
- Speak clearly and concisely
- If asked who you are, say you're an assistant calling on behalf of {user_name}

Please proceed by greeting the person who answered the call."""

    def _build_callee_system_prompt(
        self,
        provider_name: str,
        user_name: str,
        objective: str,
    ) -> str:
        """
        Build comprehensive system prompt for callee mode.

        Creates a persistent system message that keeps the agent grounded
        throughout the conversation with clear role, objective, and format.

        Args:
            provider_name: Name of the provider being called
            user_name: Name of the user on whose behalf we're calling
            objective: What we're trying to accomplish

        Returns:
            Formatted system prompt string
        """
        return f"""You are an AI assistant on a phone call.

CURRENT CALL:
- Speaking to: {provider_name}
- Calling on behalf of: {user_name}
- Objective: {objective}

YOUR ROLE:
- You are talking TO {provider_name} (the callee)
- You represent {user_name} (the owner)
- Work toward completing the objective above

CONVERSATION FORMAT:
- Messages labeled [{provider_name}]: are from the person you're speaking with - RESPOND to these
- Messages labeled [{user_name} - background]: are from the owner listening in - incorporate if relevant
- Stay focused on {provider_name} unless the owner provides critical updates
- IMPORTANT: Do NOT include speaker labels like [{provider_name}]: in YOUR responses - just speak naturally

GUIDELINES:
- Be professional and concise
- Confirm important details (times, dates, names, prices)
- If asked who you are, say you're an assistant calling on behalf of {user_name}
- If {provider_name} asks a question, answer it directly
- If you need information you don't have, ask {provider_name} or note that you'll confirm with {user_name}

LANGUAGE:
- Match the language used by {provider_name}
- If they speak Hindi, respond in Hindi (formal 'aap')

Begin by greeting {provider_name} professionally and stating your purpose."""

    def _build_call_summary(self) -> Optional[str]:
        """
        Build a summary of the call that just ended.

        Returns:
            Call summary string or None if no call context
        """
        if not self._callee_mode_context:
            return None

        provider_name = self._callee_mode_context.get("provider_name", "the provider")
        objective = self._callee_mode_context.get("objective", "unknown")
        duration = None

        if self._current_call and self._current_call.duration_seconds:
            duration = self._current_call.duration_seconds

        return f"Call with {provider_name} ended. Objective was: {objective}. Duration: {duration or 'unknown'} seconds."

    def _build_user_mode_transition_prompt(self, call_summary: str) -> str:
        """
        Build transition prompt when switching back to user mode.

        This informs the agent that the third-party call ended and
        it should now report back to the user.

        Args:
            call_summary: Summary of the call that just ended

        Returns:
            Formatted transition prompt
        """
        user_name = getattr(self.user_state, "user_name", "the user")

        return f"""The call has ended. {call_summary}

IMPORTANT MODE SWITCH: You are now speaking to {user_name} again (the original user), not the provider.

Please summarize what happened during the call to {user_name}:
- What was the outcome of the call?
- Did you successfully complete the objective?
- What are the next steps or important details?

Keep your summary concise and helpful."""

    def get_callee_mode_instructions(self) -> Optional[str]:
        """
        Get additional instructions for callee mode (for create_agent fallback).

        Note: This is a fallback method. The primary mechanism for callee mode
        is dynamic injection via _switch_to_callee_mode() which uses
        session.generate_reply(instructions=...) to update the running agent.

        Returns:
            Instructions string for callee mode, or None if not in callee mode
        """
        if not self._is_callee_mode or not self._callee_mode_context:
            return None

        provider_name = self._callee_mode_context.get("provider_name", "the provider")
        user_name = self._callee_mode_context.get("user_name", "the user")
        objective = self._callee_mode_context.get("objective", "inquire about services")

        return self._build_callee_mode_prompt(provider_name, user_name, objective)

    @property
    def is_callee_mode(self) -> bool:
        """Check if agent is in callee mode (talking to third party)."""
        return getattr(self, "_is_callee_mode", False)

    # -------------------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------------------

    async def end_call(self, reason: str = "completed") -> str:
        """End the call and cleanup SuperKik resources."""
        if self._user_preferences:
            await self._save_user_preferences()

        if self._current_call:
            from super.core.voice.superkik.tools.telephony import end_call_impl

            await end_call_impl(self)

        if self._tool_registry:
            await self._tool_registry.cleanup_all()

        if self._backbone:
            await self._backbone.cleanup()

        return await super().end_call(reason)

    async def _save_user_preferences(self) -> None:
        """Save user preferences to storage."""
        if not self._user_preferences:
            return

        if self._provider_history:
            self._user_preferences.history = self._provider_history

        self._logger.debug(
            f"User preferences would be saved for {self._user_preferences.user_id}"
        )
