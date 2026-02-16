"""
SuperkikAgentHandler - LiveKit agent handler using superkik native bindings.

This handler integrates superkik's Rust-based agent with LiveKit for both
voice and chat modalities. Uses PyO3 native bindings (no subprocess).

Features:
- Superkik session management via native PyO3 bindings
- Event bridging: superkik events → LiveKit chat/voice output
- Dual modality support (TEXT and TEXT_AUDIO)
- Tool integration via superkik's tool registry
- Callback support for message persistence
- Uses LiveKitRoomMixin for shared room I/O infrastructure

Usage (Executor Pattern):
    from super.core.voice.superkik import SuperkikAgentHandler

    handler = SuperkikAgentHandler(
        callback=MessageCallBack(),
        model_config=model_config,
        agent_name=AGENT_NAME,
    )
    handler.execute_agent()

Usage (Direct LiveKit):
    from super.core.voice.superkik import SuperkikAgentHandler
    from livekit.agents import cli, WorkerOptions

    handler = SuperkikAgentHandler(session_id="test")
    cli.run_app(WorkerOptions(entrypoint_fnc=handler.entrypoint))

Environment:
    AGENT_PROVIDER=superkik  # Enable this handler
"""

from __future__ import annotations

import asyncio
import atexit
import gc
import json
import logging
import os
import signal
from typing import TYPE_CHECKING, Any, List, Optional

from super.core.voice.base_agent_handler import BaseAgentHandler, AgentConfigResult
from super.core.voice.common.room_mixin import (
    LiveKitRoomMixin,
    TOPIC_LK_CHAT,
    TOPIC_LK_STREAM,
    TOPIC_LK_BLOCK_RESPONSE,
    TOPIC_SUPERKIK_CARDS,
)
from super.core.voice.schema import Modality, UserState

if TYPE_CHECKING:
    from livekit.agents import JobContext
    from livekit import rtc
    from super.core.callback.base import BaseCallback

# Lazy import for superkik bindings to allow graceful degradation
_SUPERKIK_AVAILABLE = False
try:
    from superkik import Superkik, Thread, ThreadEvent, ApprovalPolicy, SandboxPolicy

    _SUPERKIK_AVAILABLE = True
except ImportError:
    pass


class SuperkikAgentHandler(BaseAgentHandler, LiveKitRoomMixin):
    """
    LiveKit agent handler using superkik native PyO3 bindings.

    Bridges superkik's streaming events to LiveKit's chat and voice outputs.
    Supports both TEXT (chat-only) and TEXT_AUDIO (voice+chat) modalities.

    Uses LiveKitRoomMixin for:
    - Text I/O via lk.chat topic
    - Stream/block publishing (lk.stream, lk.block_response)
    - Card publishing (superkik.cards)
    - RPC communication (request_location)
    - Agent state signaling
    """

    def __init__(
        self,
        callback: Optional["BaseCallback"] = None,
        model_config: Optional[Any] = None,
        agent_name: Optional[str] = None,
        session_id: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """
        Initialize SuperkikAgentHandler.

        Args:
            callback: Callback for message persistence (optional)
            model_config: Model configuration object or dict (optional)
            agent_name: Agent identifier name (optional)
            session_id: Unique session identifier
            logger: Logger instance (defaults to livekit.voice.superkik)
        """
        super().__init__(
            session_id=session_id,
            logger=logger or logging.getLogger("livekit.voice.superkik"),
            handler_type="superkik",
        )
        # Initialize mixin state
        self._init_room_mixin()

        self._callback = callback
        self._model_config = model_config
        self._agent_name = agent_name or os.getenv("AGENT_NAME", "superkik-agent")
        self._superkik_client: Optional[Superkik] = None
        self._superkik_thread: Optional[Thread] = None
        self._event_task: Optional[asyncio.Task] = None
        self._room: Optional[rtc.Room] = None
        self._session = None  # For mixin compatibility
        self._tts_service: Optional[Any] = None
        self._user_state: Optional[UserState] = None
        self._is_processing: bool = False
        self._current_message_id: str = ""
        self._current_chunk_index: int = 0
        self._pending_cards: List[dict] = []

    async def entrypoint(self, ctx: "JobContext") -> None:
        """
        Main entry point called by LiveKit agent worker.

        Args:
            ctx: LiveKit JobContext with room, participant info, and metadata
        """
        if not _SUPERKIK_AVAILABLE:
            self._logger.error(
                "superkik package not available. Install with: pip install superkik"
            )
            return

        await ctx.connect()
        self._job_context = ctx
        self._room = ctx.room

        # Parse metadata
        metadata = json.loads(ctx.job.metadata) if ctx.job.metadata else {}
        self._logger.info(f"[SUPERKIK] Job metadata: {json.dumps(metadata, indent=2)}")

        # Use passed model_config or resolve from metadata
        config_result: Optional[AgentConfigResult] = None

        if self._model_config:
            # Use model_config passed at initialization
            model_config_dict = (
                self._model_config.config
                if hasattr(self._model_config, "config")
                else self._model_config
            )
            config_result = AgentConfigResult(
                model_config=model_config_dict,
                user_data=metadata.get("data", {}),
                pilot_data=None,
                participant=None,
                call_type=metadata.get("call_type", "inbound"),
            )
            self._logger.info("[SUPERKIK] Using passed model_config")
        else:
            # Resolve agent configuration from metadata
            config_result = await self._resolve_agent_config(ctx, metadata)

        if not config_result:
            self._logger.error("[SUPERKIK] Failed to resolve agent config")
            return

        # Build user state
        self._user_state = self._build_user_state(ctx, config_result, metadata)
        self._logger.info(
            f"[SUPERKIK] User state: modality={self._user_state.modality}, "
            f"thread_id={self._user_state.thread_id}"
        )

        # Initialize superkik session
        await self._init_superkik_session(config_result)

        # Initialize voice services if needed
        if self._user_state.modality == Modality.TEXT_AUDIO:
            await self._init_voice_services(config_result)

        # Setup room event handlers using mixin
        await self._setup_room_events(ctx)

        # Send first message if configured
        first_message = config_result.model_config.get("first_message")
        if first_message:
            await self._send_agent_message(first_message)

        # Wait for completion (room disconnect or shutdown)
        try:
            await self.wait_for_disconnect()
        finally:
            await self.shutdown()

    # =========================================================================
    # LiveKitRoomMixin Abstract Method Implementations
    # =========================================================================

    async def on_text_message(self, text: str, metadata: dict) -> None:
        """
        Handle incoming text message from lk.chat topic.

        Implements LiveKitRoomMixin.on_text_message.

        Args:
            text: Message text content
            metadata: Additional metadata (participant, block_data, files)
        """
        self._logger.info(f"[SUPERKIK] Processing message: {text[:100]}...")
        await self.handle_message(text)

    async def on_user_speech(self, text: str) -> None:
        """
        Handle STT result in voice mode.

        Implements LiveKitRoomMixin.on_user_speech.

        Args:
            text: Transcribed speech text
        """
        self._logger.info(f"[SUPERKIK] User speech: {text[:100]}...")
        await self.handle_message(text)

    async def on_interrupt(self) -> None:
        """
        Handle user interrupt.

        Implements LiveKitRoomMixin.on_interrupt.
        """
        await self.handle_interrupt()

    # =========================================================================
    # Message Handling
    # =========================================================================

    async def handle_message(self, text: str) -> None:
        """
        Handle an incoming text message from the user.

        Args:
            text: User's message text
        """
        if not self._superkik_thread:
            self._logger.error("[SUPERKIK] No thread available")
            return

        if self._is_processing:
            self._logger.warning("[SUPERKIK] Already processing, ignoring message")
            return

        self._is_processing = True
        self._current_message_id = self.generate_message_id()
        self._current_chunk_index = 0
        self._pending_cards = []

        try:
            await self.signal_agent_state("thinking")

            # Persist user message
            self._send_callback(text, role="user")

            # Stream events from superkik
            message_buffer = ""
            async for event in self._superkik_thread.run_streamed(text):
                delta, is_complete = await self._handle_superkik_event(event)
                if delta:
                    message_buffer += delta
                if is_complete:
                    break

            # Send final response block with accumulated cards
            if message_buffer:
                await self._send_final_response(message_buffer)

        except Exception as e:
            self._logger.error(f"[SUPERKIK] Message handling error: {e}")
            await self._send_agent_message(
                "I'm sorry, I encountered an error. Please try again."
            )
        finally:
            self._is_processing = False
            await self.signal_agent_state("listening")

    async def handle_interrupt(self) -> None:
        """
        Handle user interrupt (e.g., user starts speaking).

        Cancels ongoing generation and TTS playback.
        """
        if self._superkik_thread:
            try:
                await self._superkik_thread.interrupt()
                self._logger.info("[SUPERKIK] Turn interrupted")
            except Exception as e:
                self._logger.warning(f"[SUPERKIK] Interrupt error: {e}")

        if self._tts_service and hasattr(self._tts_service, "cancel"):
            try:
                await self._tts_service.cancel()
            except Exception:
                pass

        self._is_processing = False
        self._current_chunk_index = 0

    async def shutdown(self) -> None:
        """Gracefully shutdown the handler and superkik session."""
        self._is_shutting_down = True

        # Cancel pending tasks
        await self._cancel_pending_tasks()

        # Shutdown superkik thread
        if self._superkik_thread:
            try:
                await self._superkik_thread.shutdown()
            except Exception as e:
                self._logger.warning(f"[SUPERKIK] Thread shutdown error: {e}")
            self._superkik_thread = None

        self._superkik_client = None
        self._event_bridge = None
        self._logger.info("[SUPERKIK] Handler shutdown complete")

    # =========================================================================
    # Private Methods - Superkik Integration
    # =========================================================================

    async def _init_superkik_session(self, config: AgentConfigResult) -> None:
        """
        Initialize superkik client and thread.

        Args:
            config: Resolved agent configuration
        """
        model_config = config.model_config

        # Get model and system prompt
        model = model_config.get("model", "claude-sonnet-4-20250514")
        system_prompt = model_config.get("script") or model_config.get("system_prompt")
        persona = model_config.get("persona")
        cwd = model_config.get("cwd", os.getcwd())

        # Create superkik config
        from superkik import SuperkikConfig, ApprovalPolicy, SandboxPolicy

        sk_config = SuperkikConfig(
            model=model,
            cwd=cwd,
            approval_policy=ApprovalPolicy.NEVER,
            sandbox_policy=SandboxPolicy.FULL,
            system_prompt=system_prompt,
        )

        # Create client
        self._superkik_client = Superkik(config=sk_config)

        # Start thread with persona if specified
        self._superkik_thread = self._superkik_client.start_thread(
            persona=persona,
        )

        self._logger.info(
            f"[SUPERKIK] Session initialized: model={model}, "
            f"persona={persona or 'default'}, cwd={cwd}"
        )

    async def _init_voice_services(self, config: AgentConfigResult) -> None:
        """
        Initialize TTS and other voice services for TEXT_AUDIO modality.

        Args:
            config: Resolved agent configuration
        """
        # Get cached services from ServiceCache
        cache = self.get_service_cache()
        model_config = config.model_config

        # TODO: Initialize TTS service from cache or create new
        # For now, we'll handle voice output through LiveKit's native mechanisms
        self._logger.info("[SUPERKIK] Voice services initialization (TTS placeholder)")

    async def _setup_room_events(self, ctx: "JobContext") -> None:
        """
        Setup LiveKit room event handlers using LiveKitRoomMixin.

        Args:
            ctx: LiveKit JobContext
        """
        room = ctx.room

        # Use mixin's event bridge setup
        self.setup_event_bridge(room, topics=[TOPIC_LK_CHAT])

        # Setup additional data channel handlers
        self.setup_data_channel_handler(ctx)

        # Setup participant disconnected handler
        @room.on("participant_disconnected")
        def on_participant_disconnected(participant):
            self._logger.info(
                f"[SUPERKIK] Participant disconnected: {participant.sid}"
            )
            if not self._is_shutting_down:
                asyncio.create_task(self.shutdown())

        self._logger.info(
            f"[SUPERKIK] Room events configured via mixin for topic: {TOPIC_LK_CHAT}"
        )

    async def _handle_superkik_event(
        self, event: "ThreadEvent"
    ) -> tuple[str, bool]:
        """
        Handle a superkik event and bridge to LiveKit.

        Args:
            event: ThreadEvent from superkik

        Returns:
            Tuple of (delta_text, is_complete)
        """
        event_type = event.type
        delta = ""
        is_complete = False

        if event_type == "agent_message_delta":
            delta = event.delta
            # Stream delta to chat via mixin
            await self.send_text_delta(delta)
            # Also publish as stream block for UI
            await self.publish_stream_delta(
                message_id=self._current_message_id,
                content=delta,
                chunk_index=self._current_chunk_index,
                pilot=self._agent_name,
            )
            self._current_chunk_index += 1

        elif event_type == "agent_message":
            # Full message (non-streaming) - handle as complete
            delta = event.message
            is_complete = True

        elif event_type == "tool_call_begin":
            tool_name = event.data.get("tool_name", "")
            self._logger.info(f"[SUPERKIK] Tool call: {tool_name}")
            await self.signal_agent_state("thinking")

        elif event_type == "tool_call_end":
            success = event.data.get("success", False)
            output = event.data.get("output", "")
            self._logger.info(f"[SUPERKIK] Tool result: success={success}")

            # Check if tool returned cards
            cards = event.data.get("cards")
            if cards:
                await self._handle_tool_cards(cards)

        elif event_type == "task_complete":
            self._logger.info("[SUPERKIK] Task complete")
            is_complete = True

        elif event_type == "error":
            error_msg = event.data.get("message", "Unknown error")
            self._logger.error(f"[SUPERKIK] Error: {error_msg}")

        elif event_type == "warning":
            warning_msg = event.data.get("message", "")
            self._logger.warning(f"[SUPERKIK] Warning: {warning_msg}")

        return delta, is_complete

    async def _handle_tool_cards(self, cards: List[dict]) -> None:
        """
        Handle cards returned from tool execution.

        Publishes cards to superkik.cards topic for real-time UI updates
        and stores them for inclusion in the response block.

        Args:
            cards: List of card data from tool
        """
        for card in cards:
            card_type = card.get("type", "unknown")
            items = card.get("items", [])

            # Publish card immediately for real-time UI
            await self.publish_card(
                card_type=card_type,
                items=items,
                message_id=self._current_message_id,
                query=card.get("query"),
            )

            # Store for response block
            self._pending_cards.append({
                "type": card_type,
                "items": items,
                "count": len(items),
                "query": card.get("query"),
                "message_id": self._current_message_id,
            })

    async def _send_final_response(self, message: str) -> None:
        """
        Send final response with accumulated cards.

        Args:
            message: Full response text
        """
        # Send text message
        await self.send_text_message(message)

        # Publish response block with cards
        await self.publish_response_block(
            message_id=self._current_message_id,
            content=message,
            pilot=self._agent_name,
            cards=self._pending_cards if self._pending_cards else None,
            execution_type="tool_call" if self._pending_cards else "direct",
        )

        # Persist via callback
        self._send_callback(message, role="assistant")

        # Handle TTS if voice mode
        if (
            self._tts_service
            and self._user_state
            and self._user_state.modality == Modality.TEXT_AUDIO
        ):
            try:
                if hasattr(self._tts_service, "synthesize_and_play"):
                    await self._tts_service.synthesize_and_play(message)
            except Exception as e:
                self._logger.warning(f"[SUPERKIK] TTS synthesis error: {e}")

    async def _send_agent_message(self, message: str) -> None:
        """
        Send a complete message (for first_message, errors, etc.).

        Args:
            message: Full message to send
        """
        message_id = self.generate_message_id()

        # Send text message
        await self.send_text_message(message)

        # Publish response block
        await self.publish_response_block(
            message_id=message_id,
            content=message,
            pilot=self._agent_name,
        )

        # Persist via callback
        self._send_callback(message, role="assistant")

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _build_user_state(
        self,
        ctx: "JobContext",
        config: AgentConfigResult,
        metadata: dict,
    ) -> UserState:
        """
        Build UserState from configuration.

        Args:
            ctx: LiveKit JobContext
            config: Resolved agent configuration
            metadata: Original job metadata

        Returns:
            Populated UserState
        """
        user_data = config.user_data or {}
        model_config = config.model_config

        # Determine modality
        modality_str = metadata.get("modality", "text_audio")
        modality = Modality.TEXT if modality_str == "text" else Modality.TEXT_AUDIO

        return UserState(
            user_name=user_data.get("user_name", "User"),
            space_name=user_data.get("space_name", "Superkik"),
            contact_number=user_data.get("contact_number"),
            token=user_data.get("token", ""),
            thread_id=user_data.get("thread_id", ""),
            model_config=model_config,
            participant=config.participant,
            persona=model_config.get("persona"),
            system_prompt=model_config.get("script")
            or model_config.get("system_prompt"),
            first_message=model_config.get("first_message"),
            room_name=ctx.room.name if ctx.room else None,
            modality=modality,
        )

    def _send_callback(self, message: str, role: str = "assistant") -> None:
        """
        Send message to callback for persistence.

        Args:
            message: Message content
            role: Message role (assistant or user)
        """
        if not self._callback:
            return

        thread_id = ""
        if self._user_state:
            thread_id = self._user_state.thread_id

        try:
            from super.core.context.schema import Message

            if role == "assistant":
                msg = Message.add_assistant_message(message)
            else:
                msg = Message.add_user_message(message)

            self._callback.send(msg, thread_id)
        except Exception as e:
            self._logger.warning(f"[SUPERKIK] Callback error: {e}")

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(signum: int, _frame: Any) -> None:
            sig_name = signal.Signals(signum).name
            self._logger.info(
                f"[SUPERKIK] Received {sig_name}, initiating shutdown..."
            )
            self._is_shutting_down = True

        # Handle common termination signals
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                signal.signal(sig, signal_handler)
            except (ValueError, OSError) as e:
                # Signal handling may fail in non-main threads
                self._logger.debug(
                    f"[SUPERKIK] Could not set {sig.name} handler: {e}"
                )

    def _sync_cleanup(self) -> None:
        """Synchronous cleanup for atexit handler."""
        try:
            self._logger.info("[SUPERKIK] Running sync cleanup...")

            # Clear superkik references
            self._superkik_thread = None
            self._superkik_client = None
            self._room = None
            self._tts_service = None
            self._event_bridge = None

            # Clear service cache
            try:
                cache = self.get_service_cache()
                if cache:
                    cache.clear()
            except Exception:
                pass

            # Force garbage collection
            gc.collect()

            self._logger.info("[SUPERKIK] Sync cleanup completed")
        except Exception as e:
            self._logger.error(f"[SUPERKIK] Error during sync cleanup: {e}")

    def execute_agent(self) -> None:
        """
        Execute the agent using LiveKit CLI.

        This is the main entry point when using the executor pattern.
        Starts the LiveKit worker with this handler's entrypoint.

        Features:
        - Signal handlers for graceful shutdown (SIGTERM, SIGINT)
        - atexit cleanup registration
        - Optional prewarm for faster startup (VAD/embedding preloading)
        - Configurable process pool size
        """
        from livekit.agents import cli, WorkerOptions
        from super.core.voice.services import livekit_services

        self._logger.info(f"[SUPERKIK] Starting agent: {self._agent_name}")

        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()

        # Register atexit handler for cleanup on process exit
        atexit.register(self._sync_cleanup)

        # Preload LiveKit plugins on the main thread to avoid registration errors
        livekit_services._ensure_livekit_plugins_loaded(self._logger)

        # Check if prewarm is enabled (default: false for superkik, uses its own init)
        enable_prewarm = (
            os.getenv("SUPERKIK_ENABLE_PREWARM", "false").lower() == "true"
        )
        prewarm_fnc = None

        if enable_prewarm:
            try:
                from super.core.voice.voice_agent_handler import prewarm_process

                prewarm_fnc = prewarm_process
                self._logger.info("[SUPERKIK] Prewarm enabled")
            except ImportError:
                self._logger.warning("[SUPERKIK] Prewarm requested but not available")

        try:
            cli.run_app(
                WorkerOptions(
                    entrypoint_fnc=self.entrypoint,
                    agent_name=self._agent_name,
                    initialize_process_timeout=float(
                        os.getenv("SUPERKIK_PROCESS_TIMEOUT", "60.0")
                    ),
                    prewarm_fnc=prewarm_fnc,
                    num_idle_processes=int(
                        os.getenv("SUPERKIK_NUM_IDLE_PROCESSES", "1")
                    ),
                )
            )
        finally:
            # Ensure cleanup on normal exit
            self._sync_cleanup()
