"""
LiveKit Room Mixin - Reusable LiveKit room I/O infrastructure.

This mixin provides common LiveKit room communication patterns that can be
used by any agent handler (SuperkikAgentHandler, LiveKitLiteHandler, etc.).

Features:
- Text I/O via lk.chat topic with TextInputOptions
- Voice I/O with audio input/output options
- Stream/block publishing (lk.stream, lk.block_response)
- Card publishing (superkik.cards)
- RPC communication (perform_rpc, request_location)
- Event bridging via LiveKitEventBridge

Usage:
    class MyHandler(BaseAgentHandler, LiveKitRoomMixin):
        async def on_text_message(self, text: str, metadata: dict) -> None:
            # Handle incoming text message
            ...
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from abc import abstractmethod
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
)

if TYPE_CHECKING:
    from livekit import rtc
    from livekit.agents import JobContext
    from livekit.agents.voice import AgentSession, room_io

# Topic constants
TOPIC_LK_CHAT = "lk.chat"
TOPIC_LK_STREAM = "lk.stream"
TOPIC_LK_BLOCK_RESPONSE = "lk.block_response"
TOPIC_SUPERKIK_CARDS = "superkik.cards"
TOPIC_USER_ACTION = "user_action"


class LiveKitRoomMixin:
    """
    Mixin providing LiveKit room I/O for agent handlers.

    Covers both TEXT and TEXT_AUDIO modalities with:
    - Text input/output via lk.chat topic
    - Voice I/O via audio tracks
    - Data channel bridging via EventBridge
    - Stream/block publishing for real-time UI updates
    - Card publishing for structured data
    - RPC for frontend communication
    - Agent state signaling

    Required attributes from handler:
        _room: Optional[rtc.Room]
        _logger: logging.Logger

    Abstract methods handler must implement:
        on_text_message(text, metadata) - Handle incoming text
        on_user_speech(text) - Handle STT result (voice mode)
        on_interrupt() - Handle user interrupt
    """

    # === Required from handler (type hints for IDE) ===
    _room: Optional["rtc.Room"]
    _logger: logging.Logger
    _session: Optional["AgentSession"]

    # === Mixin state ===
    _event_bridge: Optional[Any]  # LiveKitEventBridge
    _is_text_only: bool
    _mixin_initialized: bool
    _user_action_handlers: List[Callable[[dict], Awaitable[None]]]

    def _init_room_mixin(self) -> None:
        """Initialize mixin state. Call from handler __init__."""
        self._event_bridge = None
        self._is_text_only = False
        self._mixin_initialized = False
        self._user_action_handlers = []

    # =========================================================================
    # Abstract Methods - Handler Must Implement
    # =========================================================================

    @abstractmethod
    async def on_text_message(self, text: str, metadata: dict) -> None:
        """
        Handle incoming text message from lk.chat topic.

        Args:
            text: Message text content
            metadata: Additional metadata (participant, block_data, files)
        """
        ...

    @abstractmethod
    async def on_user_speech(self, text: str) -> None:
        """
        Handle STT result in voice mode.

        Args:
            text: Transcribed speech text
        """
        ...

    @abstractmethod
    async def on_interrupt(self) -> None:
        """Handle user interrupt (user starts speaking while agent responds)."""
        ...

    # =========================================================================
    # Room Setup Methods
    # =========================================================================

    def build_room_options(
        self,
        is_text_only: bool = False,
        enable_noise_cancellation: bool = True,
        close_on_disconnect: bool = True,
        **kwargs: Any,
    ) -> "room_io.RoomOptions":
        """
        Build RoomOptions for AgentSession.start().

        Args:
            is_text_only: True for TEXT mode (disables audio)
            enable_noise_cancellation: Enable BVC noise cancellation (voice mode)
            close_on_disconnect: Close session when participant disconnects
            **kwargs: Additional RoomOptions parameters

        Returns:
            Configured RoomOptions instance
        """
        from livekit.agents.voice import room_io

        self._is_text_only = is_text_only
        room_opts_kwargs: Dict[str, Any] = {}

        if is_text_only:
            # Text-only mode: disable audio, enable text input
            self._logger.info("[ROOM_MIXIN] Configuring text-only mode")
            room_opts_kwargs["audio_input"] = False
            room_opts_kwargs["audio_output"] = False

            # Set up text input handler
            text_input_handler = self.create_text_input_handler()
            room_opts_kwargs["text_input"] = room_io.TextInputOptions(
                text_input_cb=text_input_handler
            )
        else:
            # Voice mode: configure audio options
            self._logger.info("[ROOM_MIXIN] Configuring voice mode")
            if enable_noise_cancellation:
                audio_input = self.create_audio_input_options(enable_nc=True)
                if audio_input:
                    room_opts_kwargs["audio_input"] = audio_input

        room_opts_kwargs["close_on_disconnect"] = close_on_disconnect
        room_opts_kwargs.update(kwargs)

        return room_io.RoomOptions(**room_opts_kwargs)

    def setup_event_bridge(
        self,
        room: "rtc.Room",
        topics: Optional[List[str]] = None,
    ) -> None:
        """
        Initialize LiveKitEventBridge for data channel handling.

        Args:
            room: LiveKit room instance
            topics: Topics to register for text stream handling
        """
        from super.core.voice.livekit.event_bridge import LiveKitEventBridge

        if topics is None:
            topics = [TOPIC_LK_CHAT]

        self._event_bridge = LiveKitEventBridge(logger=self._logger)
        self._event_bridge.set_room(room)
        self._event_bridge.register_text_stream_handlers(topics)

        # Register topic handlers
        self._event_bridge.on_topic(TOPIC_LK_CHAT, self._handle_chat_topic_event)

        self._logger.info(
            f"[ROOM_MIXIN] EventBridge configured for topics: {topics}"
        )

    def setup_data_channel_handler(
        self,
        ctx: "JobContext",
        additional_topics: Optional[List[str]] = None,
    ) -> None:
        """
        Setup data channel handler for custom topics.

        Registers handlers for:
        - user_action: User interactions from frontend
        - Additional custom topics

        Args:
            ctx: LiveKit JobContext
            additional_topics: Additional topics to handle
        """
        if not self._event_bridge:
            self._logger.warning(
                "[ROOM_MIXIN] EventBridge not initialized, skipping data channel setup"
            )
            return

        # Register user_action handler
        self._event_bridge.on_topic(
            TOPIC_USER_ACTION, self._handle_user_action_event
        )

        # Register additional topics
        if additional_topics:
            for topic in additional_topics:
                self._event_bridge.register_text_stream_handlers([topic])

        self._logger.info("[ROOM_MIXIN] Data channel handlers configured")

    # =========================================================================
    # Text I/O Methods
    # =========================================================================

    def create_text_input_handler(self) -> Callable:
        """
        Create text input handler for TextInputOptions.

        Returns:
            Callback function for TextInputOptions.text_input_cb
        """
        from livekit.agents.voice import room_io

        def text_input_handler(
            session: "AgentSession", event: "room_io.TextInputEvent"
        ) -> None:
            """Handle text input from lk.chat topic."""
            raw_message = event.text
            self._logger.info(
                f"[ROOM_MIXIN] Text input received: {raw_message[:100]}..."
            )

            if not raw_message or not raw_message.strip():
                return

            # Parse message - extract content from block JSON if present
            message, block_data, files = self.parse_block_message(raw_message)

            if not message or not message.strip():
                self._logger.warning("[ROOM_MIXIN] No content extracted, skipping")
                return

            # Build metadata
            metadata = {
                "block_data": block_data,
                "files": files,
                "raw_message": raw_message,
            }

            # Dispatch to handler (run in task to not block)
            asyncio.create_task(self.on_text_message(message, metadata))

        return text_input_handler

    def parse_block_message(
        self, raw_message: str
    ) -> Tuple[str, Optional[dict], List[dict]]:
        """
        Parse message - extract content and files from block JSON if present.

        Handles formats:
        - Plain text: "Hello world"
        - Block JSON: {"content": "Hello", "files": [...]}
        - Nested: {"data": {"content": "Hello"}}

        Args:
            raw_message: Raw message string

        Returns:
            Tuple of (content, block_data, files)
        """
        content = raw_message
        block_data = None
        files: List[dict] = []

        # Try to parse as JSON block
        try:
            data = json.loads(raw_message)
            if isinstance(data, dict):
                block_data = data

                # Extract content from various formats
                if "content" in data:
                    content = data["content"]
                elif "text" in data:
                    content = data["text"]
                elif "message" in data:
                    content = data["message"]
                elif "data" in data and isinstance(data["data"], dict):
                    nested = data["data"]
                    content = nested.get("content") or nested.get("text", content)

                # Extract files if present
                files = data.get("files", [])

        except (json.JSONDecodeError, TypeError):
            # Plain text message
            pass

        return content.strip() if content else "", block_data, files

    async def send_text_message(self, text: str, topic: str = TOPIC_LK_CHAT) -> None:
        """
        Send text message via data channel.

        Args:
            text: Message text
            topic: Topic to publish to (default: lk.chat)
        """
        if not self._room:
            self._logger.warning("[ROOM_MIXIN] No room available for send_text_message")
            return

        try:
            payload = json.dumps({"type": "message", "text": text}).encode()
            await self._room.local_participant.publish_data(
                payload=payload,
                topic=topic,
            )
        except Exception as e:
            self._logger.warning(f"[ROOM_MIXIN] Failed to send text message: {e}")

    async def send_text_delta(self, delta: str, topic: str = TOPIC_LK_CHAT) -> None:
        """
        Send text delta (streaming chunk) via data channel.

        Args:
            delta: Text delta/chunk
            topic: Topic to publish to (default: lk.chat)
        """
        if not self._room:
            return

        try:
            payload = json.dumps({"type": "delta", "text": delta}).encode()
            await self._room.local_participant.publish_data(
                payload=payload,
                topic=topic,
            )
        except Exception as e:
            self._logger.warning(f"[ROOM_MIXIN] Failed to send delta: {e}")

    # =========================================================================
    # Voice I/O Methods
    # =========================================================================

    def create_audio_input_options(
        self, enable_nc: bool = True
    ) -> Optional["room_io.AudioInputOptions"]:
        """
        Create audio input options with optional noise cancellation.

        Args:
            enable_nc: Enable BVC noise cancellation

        Returns:
            AudioInputOptions or None if NC not available
        """
        if not enable_nc:
            return None

        try:
            from livekit.agents.voice import room_io
            from livekit.plugins import noise_cancellation

            nc = noise_cancellation.BVC()
            self._logger.info("[ROOM_MIXIN] BVC noise cancellation enabled")
            return room_io.AudioInputOptions(noise_cancellation=nc)

        except ImportError:
            self._logger.warning(
                "[ROOM_MIXIN] Noise cancellation plugin not available"
            )
            return None
        except Exception as e:
            self._logger.warning(
                f"[ROOM_MIXIN] Noise cancellation setup failed: {e}"
            )
            return None

    def create_audio_output_options(self) -> Optional["room_io.AudioOutputOptions"]:
        """
        Create audio output options.

        Returns:
            AudioOutputOptions or None
        """
        # Currently using defaults, can be extended for custom audio output
        return None

    # =========================================================================
    # Stream/Block Publishing Methods
    # =========================================================================

    async def publish_stream_delta(
        self,
        message_id: str,
        content: str,
        chunk_index: int,
        pilot: str = "agent",
        focus: Optional[str] = None,
    ) -> None:
        """
        Publish streaming chunk to lk.stream topic.

        Args:
            message_id: Unique message ID (correlates with final response)
            content: Text chunk content
            chunk_index: Ordered chunk index (0, 1, 2, ...)
            pilot: Agent/pilot name
            focus: Optional focus/context
        """
        if not self._room:
            return

        stream_block = self.build_stream_block(
            message_id=message_id,
            content=content,
            chunk_index=chunk_index,
            pilot=pilot,
            focus=focus,
        )

        try:
            await self._room.local_participant.publish_data(
                payload=json.dumps(stream_block).encode(),
                topic=TOPIC_LK_STREAM,
            )
        except Exception as e:
            self._logger.warning(f"[ROOM_MIXIN] Failed to publish stream delta: {e}")

    async def publish_response_block(
        self,
        message_id: str,
        content: str,
        pilot: str = "agent",
        cards: Optional[List[dict]] = None,
        block_type: str = "pilot_response",
        execution_type: str = "direct",
        focus: Optional[str] = None,
    ) -> None:
        """
        Publish final response block to lk.block_response topic.

        Args:
            message_id: Unique message ID
            content: Full response text
            pilot: Agent/pilot name
            cards: Optional list of card data from tool executions
            block_type: Block type (pilot_response, reply, etc.)
            execution_type: Execution type (direct, tool_call)
            focus: Optional focus/context
        """
        if not self._room:
            return

        response_block = self.build_response_block(
            message_id=message_id,
            content=content,
            pilot=pilot,
            cards=cards,
            block_type=block_type,
            execution_type=execution_type,
            focus=focus,
        )

        try:
            await self._room.local_participant.publish_data(
                payload=json.dumps(response_block).encode(),
                topic=TOPIC_LK_BLOCK_RESPONSE,
            )
        except Exception as e:
            self._logger.warning(f"[ROOM_MIXIN] Failed to publish response block: {e}")

    def build_stream_block(
        self,
        message_id: str,
        content: str,
        chunk_index: int,
        pilot: str = "agent",
        focus: Optional[str] = None,
    ) -> dict:
        """Build StreamBlock payload."""
        return {
            "event": "stream",
            "id": message_id,
            "pilot": pilot,
            "data": {
                "content": content,
                "chunk_index": chunk_index,
                "is_final": False,
                "focus": focus,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    def build_response_block(
        self,
        message_id: str,
        content: str,
        pilot: str = "agent",
        cards: Optional[List[dict]] = None,
        block_type: str = "pilot_response",
        execution_type: str = "direct",
        focus: Optional[str] = None,
    ) -> dict:
        """Build ResponseBlock payload."""
        data: Dict[str, Any] = {
            "content": content,
            "focus": focus,
        }

        if cards:
            data["cards"] = cards

        return {
            "event": "block_response",
            "id": message_id,
            "pilot": pilot,
            "execution_type": execution_type,
            "block": "html",
            "block_type": block_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

    # =========================================================================
    # Card Publishing Methods
    # =========================================================================

    async def publish_card(
        self,
        card_type: str,
        items: List[dict],
        message_id: Optional[str] = None,
        query: Optional[str] = None,
    ) -> None:
        """
        Publish card to superkik.cards topic.

        Args:
            card_type: Card type (provider, web, person, event, booking, call)
            items: List of card items
            message_id: Correlation ID (optional, auto-generated if not provided)
            query: Original search query (optional)
        """
        if not self._room:
            return

        if not message_id:
            message_id = str(uuid.uuid4())[:12]

        card_payload = self.build_card_payload(
            card_type=card_type,
            items=items,
            message_id=message_id,
            query=query,
        )

        try:
            await self._room.local_participant.publish_data(
                payload=json.dumps(card_payload).encode(),
                topic=TOPIC_SUPERKIK_CARDS,
            )
            self._logger.debug(
                f"[ROOM_MIXIN] Published {card_type} card with {len(items)} items"
            )
        except Exception as e:
            self._logger.warning(f"[ROOM_MIXIN] Failed to publish card: {e}")

    def build_card_payload(
        self,
        card_type: str,
        items: List[dict],
        message_id: str,
        query: Optional[str] = None,
    ) -> dict:
        """Build card payload for superkik.cards topic."""
        return {
            "type": card_type,
            "items": items,
            "count": len(items),
            "query": query,
            "message_id": message_id,
        }

    # =========================================================================
    # User Action Handling
    # =========================================================================

    def register_user_action_handler(
        self, handler: Callable[[dict], Awaitable[None]]
    ) -> None:
        """
        Register handler for user_action topic events.

        Args:
            handler: Async function that receives action dict
        """
        self._user_action_handlers.append(handler)

    async def _handle_user_action_event(self, event: dict) -> None:
        """Handle user_action topic events."""
        try:
            data = event.get("data", {})
            action = data.get("action", "unknown")
            self._logger.debug(f"[ROOM_MIXIN] User action: {action}")

            # Dispatch to registered handlers
            for handler in self._user_action_handlers:
                try:
                    await handler(data)
                except Exception as e:
                    self._logger.warning(
                        f"[ROOM_MIXIN] User action handler error: {e}"
                    )

        except Exception as e:
            self._logger.warning(f"[ROOM_MIXIN] Error handling user action: {e}")

    # =========================================================================
    # RPC Methods
    # =========================================================================

    async def perform_rpc(
        self,
        destination_identity: str,
        method: str,
        payload: str,
        timeout: float = 60.0,
    ) -> Optional[str]:
        """
        Perform RPC call to a remote participant.

        Use for requesting actions from frontend:
        - getLocation: Request user's coordinates
        - requestPermission: Request specific permissions
        - triggerUI: Trigger UI actions

        Args:
            destination_identity: Target participant identity
            method: RPC method name
            payload: JSON string payload
            timeout: Timeout in seconds

        Returns:
            Response string or None on error/timeout
        """
        if not self._room:
            self._logger.warning("[ROOM_MIXIN] No room available for RPC")
            return None

        try:
            response = await self._room.local_participant.perform_rpc(
                destination_identity=destination_identity,
                method=method,
                payload=payload,
            )
            self._logger.debug(
                f"[ROOM_MIXIN] RPC '{method}' returned: {response[:100]}..."
                if response and len(response) > 100
                else f"[ROOM_MIXIN] RPC '{method}' returned: {response}"
            )
            return response

        except asyncio.TimeoutError:
            self._logger.warning(
                f"[ROOM_MIXIN] RPC '{method}' timed out after {timeout}s"
            )
            return None
        except Exception as e:
            self._logger.error(f"[ROOM_MIXIN] RPC '{method}' failed: {e}")
            return None

    async def request_location(
        self,
        destination_identity: str,
        reason: str = "find nearby places",
        timeout: float = 30.0,
    ) -> Optional[dict]:
        """
        Request location from user via RPC.

        Triggers browser geolocation API on frontend.

        Args:
            destination_identity: User participant identity
            reason: Human-readable reason (shown in UI prompt)
            timeout: Timeout for user interaction

        Returns:
            Dict with {latitude, longitude, accuracy} or None
        """
        payload = json.dumps({
            "action": "request_location",
            "reason": reason,
            "data": {
                "message": f"To {reason}, I need access to your location.",
                "permissions": ["geolocation"],
                "ui": {
                    "title": "Location Required",
                    "description": f"Share your location to {reason}",
                    "button_text": "Share Location",
                    "cancel_text": "Not Now",
                },
            },
        })

        response = await self.perform_rpc(
            destination_identity=destination_identity,
            method="getLocation",
            payload=payload,
            timeout=timeout,
        )

        if not response:
            return None

        try:
            result = json.loads(response)
            if result.get("status") == "success":
                return {
                    "latitude": result.get("latitude"),
                    "longitude": result.get("longitude"),
                    "accuracy": result.get("accuracy"),
                }
            else:
                self._logger.warning(
                    f"[ROOM_MIXIN] Location denied: {result.get('error', 'unknown')}"
                )
                return None
        except json.JSONDecodeError:
            self._logger.error(f"[ROOM_MIXIN] Invalid location response: {response}")
            return None

    # =========================================================================
    # State Management
    # =========================================================================

    async def signal_agent_state(self, state: str) -> None:
        """
        Signal agent state to LiveKit via participant attributes.

        Args:
            state: State name (listening, thinking, speaking)
        """
        if not self._room:
            return

        try:
            await self._room.local_participant.set_attributes(
                {"agent.state": state}
            )
        except Exception as e:
            self._logger.warning(f"[ROOM_MIXIN] Failed to set state: {e}")

    async def wait_for_disconnect(self) -> None:
        """Wait for room disconnect event."""
        if not self._room:
            return

        disconnect_event = asyncio.Event()

        @self._room.on("disconnected")
        def on_disconnected():
            disconnect_event.set()

        await disconnect_event.wait()

    # =========================================================================
    # Event Listeners
    # =========================================================================

    def on_state_change(self, callback: Callable[[str, str], None]) -> None:
        """
        Register callback for state change events.

        Args:
            callback: Function(state: str, source: str)
        """
        if self._event_bridge:
            self._event_bridge.on_state_change(callback)

    def on_transcript(self, callback: Callable[[str, str], None]) -> None:
        """
        Register callback for transcript events (STT results).

        Args:
            callback: Function(text: str, participant: str)
        """
        if self._event_bridge:
            self._event_bridge.on_transcript(callback)

    # =========================================================================
    # Internal Event Handlers
    # =========================================================================

    async def _handle_chat_topic_event(self, event: dict) -> None:
        """
        Handle chat topic events from EventBridge.

        Called when data arrives on the 'lk.chat' topic.
        """
        try:
            parsed_data = event.get("data", {})
            raw_data = event.get("raw_data", b"")
            participant = event.get("participant_identity", "unknown")

            self._logger.debug(
                f"[ROOM_MIXIN] Chat event from {participant}: {parsed_data}"
            )

            # Extract message text
            text = self._extract_message_text(parsed_data, raw_data)

            if text:
                metadata = {
                    "participant": participant,
                    "parsed_data": parsed_data,
                }
                await self.on_text_message(text, metadata)

        except Exception as e:
            self._logger.warning(f"[ROOM_MIXIN] Error handling chat event: {e}")

    def _extract_message_text(
        self, parsed_data: dict, raw_data: bytes
    ) -> str:
        """
        Extract message text from chat event data.

        Handles multiple message formats:
        - {"type": "message", "text": "..."}
        - {"content": "..."} (block format)
        - {"message": "..."}
        - {"text": "..."}
        - Plain text in raw_data

        Args:
            parsed_data: Parsed JSON dict from event
            raw_data: Raw bytes from event

        Returns:
            Extracted message text or empty string
        """
        # Try parsed data first
        if parsed_data:
            if parsed_data.get("type") == "message":
                return parsed_data.get("text", "").strip()
            if "content" in parsed_data:
                return parsed_data.get("content", "").strip()
            if "message" in parsed_data:
                return parsed_data.get("message", "").strip()
            if "text" in parsed_data:
                return parsed_data.get("text", "").strip()

        # Fallback to raw_data as plain text
        if raw_data:
            try:
                if isinstance(raw_data, bytes):
                    return raw_data.decode("utf-8").strip()
                return str(raw_data).strip()
            except Exception:
                pass

        return ""

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def generate_message_id(self) -> str:
        """Generate unique message ID for stream/response correlation."""
        return str(uuid.uuid4())[:12]

    def get_participant_identity(self) -> Optional[str]:
        """Get first remote participant identity (for RPC calls)."""
        if not self._room:
            return None

        for participant in self._room.remote_participants.values():
            return participant.identity

        return None
