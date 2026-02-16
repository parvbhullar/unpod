"""
LiveKit Event Bridge - Universal Agent-to-LiveKit Integration.

This module provides a generic bridge for any voice agent framework (Pipecat,
LiveKit native agents, or custom implementations) to communicate state and
events to LiveKit rooms. The frontend useVoiceAssistant hook can then track:

- Agent states: listening, thinking, speaking
- User transcripts (interim and final)
- Agent transcripts
- Custom events
- Bidirectional data channel communication

Usage:
    # Create bridge instance
    bridge = LiveKitEventBridge()

    # From any agent, emit state changes
    await bridge.set_agent_state("listening")
    await bridge.set_agent_state("thinking")
    await bridge.set_agent_state("speaking")

    # Emit transcript events
    await bridge.emit_user_transcript("Hello", is_final=True)
    await bridge.emit_agent_transcript("Hi there!", is_final=True)

    # Emit custom events
    await bridge.emit_event("tool_called", {"name": "search", "args": {...}})

    # Publish data to specific topics
    await bridge.publish_data(
        {"type": "providers", "items": [...]},
        topic="superkik.providers",
        reliable=True
    )

    # Listen for incoming data from frontend
    def handle_user_action(event):
        action = event['data'].get('action')
        provider_id = event['data'].get('provider_id')
        print(f"User selected provider: {provider_id}")

    bridge.on_topic("user_action", handle_user_action)

    # Or listen to all data
    bridge.on_data_received(lambda e: print(f"Data from {e['participant_identity']}"))
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypedDict, Union

from super.core.logging import logging as app_logging


class DataReceivedEvent(TypedDict, total=False):
    """Data received event structure."""

    topic: str
    data: Dict[str, Any]
    participant_identity: Optional[str]
    participant_name: Optional[str]
    raw_data: bytes


class AgentState(str, Enum):
    """Valid LiveKit agent states for useVoiceAssistant hook."""

    INITIALIZING = "initializing"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"


class UserState(str, Enum):
    """User states for tracking user activity."""

    IDLE = "idle"
    SPEAKING = "speaking"


@dataclass
class TranscriptEvent:
    """Transcript event data structure."""

    id: int
    role: str  # "user" or "assistant"
    content: str
    is_final: bool = True
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "is_final": self.is_final,
            "timestamp": self.timestamp,
        }


@dataclass
class ConversationItem:
    """Conversation item for full conversation tracking."""

    id: str
    role: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class LiveKitEventBridge:
    """
    Universal bridge for emitting agent events to LiveKit rooms.

    This class provides a simple interface for any voice agent to communicate
    with LiveKit frontend clients via participant attributes and data channels.

    The bridge can be used in two modes:
    1. Automatic: Provide job_context at init, bridge manages LiveKit connection
    2. Manual: Call set_participant() with a LocalParticipant instance

    Example (Automatic with JobContext):
        from livekit.agents import get_job_context

        bridge = LiveKitEventBridge()
        await bridge.initialize()  # Gets JobContext automatically

        # Emit state changes
        await bridge.set_agent_state(AgentState.LISTENING)

    Example (Manual with Participant):
        bridge = LiveKitEventBridge()
        bridge.set_participant(local_participant)

        # Emit state changes
        await bridge.set_agent_state(AgentState.THINKING)
    """

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        auto_initialize: bool = True,
        emit_transcripts: bool = True,
        buffer_events: bool = True,
    ):
        """
        Initialize the LiveKit event bridge.

        Args:
            logger: Optional logger instance
            auto_initialize: Whether to auto-get JobContext on first use
            emit_transcripts: Whether to emit transcript events
            buffer_events: Whether to buffer events if not yet connected
        """
        self._logger = logger or app_logging.get_logger("livekit.event.bridge")
        self._auto_initialize = auto_initialize
        self._emit_transcripts = emit_transcripts
        self._buffer_events = buffer_events

        # LiveKit connection
        self._room = None
        self._local_participant = None
        self._job_context = None
        self._initialized = False

        # State tracking
        self._current_agent_state: AgentState = AgentState.LISTENING
        self._current_user_state: UserState = UserState.IDLE
        self._transcript_id: int = 0
        self._conversation_items: List[ConversationItem] = []

        # Event buffering for offline events
        self._event_buffer: List[Dict] = []

        # Event callbacks for local listeners
        self._state_listeners: List[Callable] = []
        self._transcript_listeners: List[Callable] = []
        self._data_listeners: List[Callable] = []
        self._topic_listeners: Dict[str, List[Callable]] = {}

    async def initialize(self, job_context=None):
        """
        Initialize the bridge with LiveKit connection.

        Args:
            job_context: Optional JobContext. If None, will try to get from
                        livekit.agents.get_job_context()
        """
        try:
            if job_context:
                self._job_context = job_context
            else:
                from livekit.agents import get_job_context

                self._job_context = get_job_context()

            if self._job_context and hasattr(self._job_context, "room"):
                self._room = self._job_context.room
                self._initialized = True
                self._logger.info("LiveKit event bridge initialized successfully")

                # Register data received handler
                self._register_data_handler()

                # Flush buffered events
                await self._flush_event_buffer()

        except Exception as e:
            self._logger.warning(f"Could not initialize LiveKit bridge: {e}")

    def set_participant(self, participant):
        """
        Manually set the local participant for event emission.

        Args:
            participant: LiveKit LocalParticipant instance
        """
        self._local_participant = participant
        self._initialized = True
        self._logger.debug("LiveKit participant set manually")

    def set_room(self, room):
        """
        Set the LiveKit room reference.

        Args:
            room: LiveKit Room instance
        """
        self._room = room
        if room and hasattr(room, "local_participant"):
            self._local_participant = room.local_participant
            self._initialized = True
            self._register_data_handler()

    @property
    def local_participant(self):
        """Get the local participant (from room or manually set)."""
        if self._room and hasattr(self._room, "local_participant"):
            return self._room.local_participant
        return self._local_participant

    async def _ensure_initialized(self):
        """Ensure bridge is initialized before emitting events."""
        if not self._initialized and self._auto_initialize:
            await self.initialize()

    async def _flush_event_buffer(self):
        """Flush any buffered events after initialization."""
        if not self._initialized or not self._event_buffer:
            return

        self._logger.debug(f"Flushing {len(self._event_buffer)} buffered events")

        for event in self._event_buffer:
            event_type = event.get("type")
            if event_type == "state":
                await self._emit_state_attribute(event.get("state"))
            elif event_type == "transcript":
                await self._emit_transcript_attribute(event.get("data"))
            elif event_type == "custom":
                await self._emit_custom_attribute(event.get("name"), event.get("data"))

        self._event_buffer.clear()

    # Output-only topics that should be skipped by data_received handler
    # These are topics we SEND data to, not receive input from.
    #
    # Note: lk.chat is NOT in this list because it's bidirectional:
    # - We receive text input from frontend via lk.chat (data channel or text stream)
    # - We send responses via lk.chat
    # The topic listener system routes lk.chat to the appropriate handler.
    _OUTPUT_ONLY_TOPICS = {
        "lk.stream",  # Output streaming topic (not input)
        "lk.agent.transcript",  # Agent transcript output (not input)
        "superkik.cards",  # Card streaming output (not input)
        "superkik.preferences",  # Preference updates output (not input)
        "superkik.session",  # Session state output (not input)
    }

    def _register_data_handler(self):
        """Register the data_received event handler on the room."""
        if not self._room:
            return

        try:
            from livekit import rtc

            @self._room.on("data_received")
            def on_data_received(data: rtc.DataPacket):
                """Handle incoming data from room participants."""
                asyncio.create_task(self._handle_data_received(data))

            self._logger.debug("Data received handler registered on room")

        except ImportError:
            self._logger.warning("livekit.rtc not available for data handler")
        except Exception as e:
            self._logger.error(f"Failed to register data handler: {e}")

    def register_text_stream_handlers(self, topics: List[str] | None = None):
        """
        Register text stream handlers for receiving text stream messages.

        Text streams are LiveKit's newer API for sending text data (vs data channels).
        This method registers handlers that route text stream messages to the same
        topic listener system as data channel messages.

        Args:
            topics: List of topics to register handlers for. If None, registers
                    handlers for common input topics: lk.chat, user_action
        """
        if not self._room:
            self._logger.warning("Cannot register text stream handlers: no room")
            return

        if topics is None:
            # Default input topics to handle via text streams
            topics = ["lk.chat", "user_action"]

        try:
            for topic in topics:
                self._register_single_text_stream_handler(topic)
            self._logger.info(
                f"[EventBridge] Text stream handlers registered for topics: {topics}"
            )
        except Exception as e:
            self._logger.error(f"Failed to register text stream handlers: {e}")

    def _register_single_text_stream_handler(self, topic: str):
        """Register a text stream handler for a single topic."""
        try:
            # Create handler that routes to topic listeners
            def handle_text_stream(reader, participant_identity: str):
                """Handle incoming text stream and route to topic listeners."""
                asyncio.create_task(
                    self._handle_text_stream_message(
                        reader, participant_identity, topic
                    )
                )

            self._room.register_text_stream_handler(topic, handle_text_stream)
            self._logger.debug(
                f"[EventBridge] Text stream handler registered for '{topic}'"
            )

        except ValueError as e:
            # Handler already registered (by RoomIO/TextInputOptions)
            self._logger.debug(
                f"[EventBridge] Text stream handler for '{topic}' already exists: {e}"
            )
        except Exception as e:
            self._logger.error(
                f"[EventBridge] Failed to register text stream handler for '{topic}': {e}"
            )

    async def _handle_text_stream_message(
        self,
        reader,
        participant_identity: str,
        topic: str,
    ):
        """
        Handle incoming text stream message and route to topic listeners.

        This provides a fallback path for text stream messages that may not be
        handled by LiveKit's built-in TextInputOptions (e.g., due to participant
        identity mismatch).

        Args:
            reader: TextStreamReader for reading the message content
            participant_identity: Identity of the sender
            topic: Topic the message was sent on
        """
        try:
            # Read the complete message
            text = await reader.read_all()

            self._logger.info(
                f"[EventBridge] Text stream received on '{topic}' "
                f"from '{participant_identity}': {text[:200]}..."
            )

            # Try to parse as JSON
            parsed_data: Dict[str, Any] = {}
            try:
                parsed_data = json.loads(text)
            except json.JSONDecodeError:
                # Not JSON - treat as plain text
                parsed_data = {"text": text, "raw": True}

            # Create event object (compatible with DataReceivedEvent)
            event: DataReceivedEvent = {
                "topic": topic,
                "data": parsed_data,
                "participant_identity": participant_identity,
                "participant_name": participant_identity,
                "raw_data": text.encode("utf-8"),
            }

            # Notify global data listeners
            await self._notify_data_listeners(event)

            # Notify topic-specific listeners
            if topic in self._topic_listeners:
                await self._notify_topic_listeners(topic, event)

        except Exception as e:
            self._logger.error(
                f"[EventBridge] Error handling text stream on '{topic}': {e}"
            )

    async def _handle_data_received(self, data_packet):
        """
        Process incoming data packet and notify listeners.

        Skips topics that are handled by other systems (e.g., lk.chat
        is handled by TextInputOptions.text_input_cb).

        Args:
            data_packet: LiveKit DataPacket with data and participant info
        """
        try:
            # Get topic first to check if we should handle it
            topic = getattr(data_packet, "topic", "") or ""

            # Skip output-only topics (these are for sending, not receiving)
            if topic in self._OUTPUT_ONLY_TOPICS:
                self._logger.debug(
                    f"[EventBridge] Skipping output-only topic '{topic}'"
                )
                return

            # Extract participant info
            participant_identity = None
            participant_name = None
            if data_packet.participant:
                participant_identity = data_packet.participant.identity
                participant_name = getattr(
                    data_packet.participant, "name", participant_identity
                )

            # Try to parse JSON data
            raw_data = data_packet.data
            parsed_data: Dict[str, Any] = {}

            try:
                if isinstance(raw_data, bytes):
                    parsed_data = json.loads(raw_data.decode("utf-8"))
                elif isinstance(raw_data, str):
                    parsed_data = json.loads(raw_data)
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Not JSON, keep as raw
                self._logger.debug(f"Received non-JSON data on topic '{topic}'")

            # Create event object
            event: DataReceivedEvent = {
                "topic": topic,
                "data": parsed_data,
                "participant_identity": participant_identity,
                "participant_name": participant_name,
                "raw_data": raw_data if isinstance(raw_data, bytes) else b"",
            }

            # Log received data with full content
            self._logger.info(
                f"[EventBridge] Data received from '{participant_identity}' "
                f"on topic '{topic}': {json.dumps(parsed_data, default=str)}"
            )

            # Notify global listeners
            await self._notify_data_listeners(event)

            # Notify topic-specific listeners
            if topic and topic in self._topic_listeners:
                await self._notify_topic_listeners(topic, event)

        except Exception as e:
            self._logger.error(f"Error handling received data: {e}")

    async def _notify_data_listeners(self, event: DataReceivedEvent):
        """Notify all global data listeners."""
        for listener in self._data_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(event)
                else:
                    listener(event)
            except Exception as e:
                self._logger.error(f"Data listener error: {e}")

    async def _notify_topic_listeners(self, topic: str, event: DataReceivedEvent):
        """Notify topic-specific listeners."""
        listeners = self._topic_listeners.get(topic, [])
        for listener in listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(event)
                else:
                    listener(event)
            except Exception as e:
                self._logger.error(f"Topic listener error for '{topic}': {e}")

    # =========================================================================
    # Agent State Management
    # =========================================================================

    async def set_agent_state(self, state: Union[AgentState, str]) -> bool:
        """
        Set the agent state and emit to LiveKit.

        Args:
            state: New agent state (AgentState enum or string)

        Returns:
            True if state was updated, False otherwise
        """
        # Normalize to string
        state_str = state.value if isinstance(state, AgentState) else state

        # Validate state
        valid_states = {s.value for s in AgentState}
        if state_str not in valid_states:
            self._logger.warning(f"Invalid agent state: {state_str}")
            return False

        # Skip if unchanged
        if state_str == self._current_agent_state.value:
            return False

        # Update local state
        self._current_agent_state = AgentState(state_str)

        # Notify local listeners
        for listener in self._state_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(state_str, "agent")
                else:
                    listener(state_str, "agent")
            except Exception as e:
                self._logger.error(f"State listener error: {e}")

        # Emit to LiveKit
        await self._ensure_initialized()

        if self._initialized:
            await self._emit_state_attribute(state_str)
        elif self._buffer_events:
            self._event_buffer.append({"type": "state", "state": state_str})

        self._logger.debug(f"Agent state changed to: {state_str}")
        return True

    async def set_user_state(self, state: Union[UserState, str]) -> bool:
        """
        Set the user state (speaking/idle).

        Args:
            state: New user state

        Returns:
            True if state was updated
        """
        state_str = state.value if isinstance(state, UserState) else state
        self._current_user_state = UserState(state_str)
        return True

    def get_agent_state(self) -> str:
        """Get the current agent state."""
        return self._current_agent_state.value

    def get_user_state(self) -> str:
        """Get the current user state."""
        return self._current_user_state.value

    async def _emit_state_attribute(self, state: str):
        """Emit agent state via participant attributes."""
        if not self.local_participant:
            return

        try:
            await self.local_participant.set_attributes({"lk.agent.state": state})
        except Exception as e:
            self._logger.error(f"Failed to emit state attribute: {e}")

    # =========================================================================
    # Transcript Events
    # =========================================================================

    async def emit_user_transcript(
        self, content: str, is_final: bool = True
    ) -> Optional[TranscriptEvent]:
        """
        Emit a user transcript event.

        Args:
            content: Transcript text
            is_final: Whether this is a final or interim transcript

        Returns:
            TranscriptEvent if emitted, None otherwise
        """
        if not self._emit_transcripts or not content:
            return None

        self._transcript_id += 1
        event = TranscriptEvent(
            id=self._transcript_id,
            role="user",
            content=content,
            is_final=is_final,
        )

        # Notify local listeners
        for listener in self._transcript_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(event)
                else:
                    listener(event)
            except Exception as e:
                self._logger.error(f"Transcript listener error: {e}")

        # Add to conversation if final
        if is_final:
            self._conversation_items.append(
                ConversationItem(
                    id=str(self._transcript_id),
                    role="user",
                    content=content,
                )
            )

        # Emit to LiveKit
        await self._ensure_initialized()

        if self._initialized:
            await self._emit_transcript_attribute(event.to_dict())
        elif self._buffer_events:
            self._event_buffer.append({"type": "transcript", "data": event.to_dict()})

        return event

    async def emit_agent_transcript(
        self, content: str, is_final: bool = True
    ) -> Optional[TranscriptEvent]:
        """
        Emit an agent/assistant transcript event.

        Args:
            content: Transcript text
            is_final: Whether this is final or streaming

        Returns:
            TranscriptEvent if emitted, None otherwise
        """
        if not self._emit_transcripts or not content:
            return None

        self._transcript_id += 1
        event = TranscriptEvent(
            id=self._transcript_id,
            role="assistant",
            content=content,
            is_final=is_final,
        )

        # Notify local listeners
        for listener in self._transcript_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(event)
                else:
                    listener(event)
            except Exception as e:
                self._logger.error(f"Transcript listener error: {e}")

        # Add to conversation if final
        if is_final:
            self._conversation_items.append(
                ConversationItem(
                    id=str(self._transcript_id),
                    role="assistant",
                    content=content,
                )
            )

        # Emit to LiveKit
        await self._ensure_initialized()

        if self._initialized:
            await self._emit_transcript_attribute(event.to_dict())
        elif self._buffer_events:
            self._event_buffer.append({"type": "transcript", "data": event.to_dict()})

        return event

    async def emit_transcript(
        self, role: str, content: str, is_final: bool = True
    ) -> Optional[TranscriptEvent]:
        """
        Emit a transcript event for any role.

        Generic method that routes to emit_user_transcript or emit_agent_transcript
        based on the role parameter.

        Args:
            role: Speaker role ("user" or "assistant")
            content: Transcript text
            is_final: Whether this is final or streaming

        Returns:
            TranscriptEvent if emitted, None otherwise
        """
        if role == "user":
            return await self.emit_user_transcript(content, is_final)
        else:
            return await self.emit_agent_transcript(content, is_final)

    async def _emit_transcript_attribute(self, data: dict):
        """Emit transcript via participant attributes."""
        if not self.local_participant:
            return

        try:
            await self.local_participant.set_attributes(
                {"lk.agent.transcript": json.dumps(data)}
            )
        except Exception as e:
            self._logger.error(f"Failed to emit transcript attribute: {e}")

    # =========================================================================
    # Custom Events
    # =========================================================================

    async def emit_event(self, event_name: str, data: Any = None):
        """
        Emit a custom event via participant attributes.

        Args:
            event_name: Name of the event
            data: Event data (will be JSON serialized)
        """
        await self._ensure_initialized()

        if self._initialized:
            await self._emit_custom_attribute(event_name, data)
        elif self._buffer_events:
            self._event_buffer.append(
                {"type": "custom", "name": event_name, "data": data}
            )

    async def _emit_custom_attribute(self, name: str, data: Any):
        """Emit custom event via participant attributes."""
        if not self.local_participant:
            return

        try:
            event_data = {
                "name": name,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
            }
            await self.local_participant.set_attributes(
                {f"lk.agent.event.{name}": json.dumps(event_data)}
            )
        except Exception as e:
            self._logger.error(f"Failed to emit custom event: {e}")

    # =========================================================================
    # Data Channel for Large JSON Messages
    # =========================================================================

    async def publish_data(
        self,
        data: Dict[str, Any],
        topic: str = "message",
        reliable: bool = True,
        destination_identities: Optional[List[str]] = None,
    ) -> bool:
        """
        Publish large JSON data via LiveKit data channel.

        Use this for MessageCallback blocks and other large JSON payloads
        that exceed attribute size limits or need reliable delivery.

        Args:
            data: Dictionary to JSON serialize and send
            topic: Topic name for filtering on frontend (default: "message")
            reliable: Use reliable delivery (default: True)
            destination_identities: Optional list of participant identities to send to

        Returns:
            True if data was published successfully
        """
        await self._ensure_initialized()

        if not self.local_participant:
            self._logger.warning("Cannot publish data: no participant available")
            return False

        try:
            # Serialize data to JSON bytes
            payload = json.dumps(data, ensure_ascii=False).encode("utf-8")

            # Publish via data channel
            await self.local_participant.publish_data(
                payload,
                reliable=reliable,
                destination_identities=destination_identities or [],
                topic=topic,
            )

            self._logger.debug(
                f"[EventBridge] Data published to topic '{topic}' with {payload}"
                f"({len(payload)} bytes, reliable={reliable})"
            )
            return True

        except Exception as e:
            self._logger.error(f"Failed to publish data: {e}")
            return False

    async def publish_message_callback(
        self,
        message: Dict[str, Any],
        destination_identities: Optional[List[str]] = None,
    ) -> bool:
        """
        Publish a MessageCallback block via data channel.

        Convenience method for sending structured message callbacks
        to the frontend.

        Args:
            message: MessageCallback dictionary with role, content, event, etc.
            destination_identities: Optional specific recipients

        Returns:
            True if message was published successfully
        """
        return await self.publish_data(
            data=message,
            topic="message_callback",
            reliable=True,
            destination_identities=destination_identities,
        )

    # =========================================================================
    # RPC (Remote Procedure Call) Methods
    # Reference: https://docs.livekit.io/transport/data/rpc/
    # =========================================================================

    async def perform_rpc(
        self,
        destination_identity: str,
        method: str,
        payload: str,
        timeout: float = 60.0,
    ) -> Optional[str]:
        """
        Perform an RPC call to a remote participant.

        Use this to request actions from the frontend (e.g., get location,
        request permissions, trigger UI actions).

        Args:
            destination_identity: Identity of the target participant
            method: RPC method name (e.g., "getLocation", "requestPermission")
            payload: JSON string payload to send
            timeout: Timeout in seconds (default 10s)

        Returns:
            Response string from the remote participant, or None on error

        Example:
            response = await bridge.perform_rpc(
                destination_identity="user-123",
                method="getLocation",
                payload='{"reason": "find nearby places"}'
            )
            if response:
                location = json.loads(response)
                lat, lng = location["latitude"], location["longitude"]
        """
        await self._ensure_initialized()

        if not self.local_participant:
            self._logger.warning("Cannot perform RPC: no local participant")
            return None

        try:
            response = await self.local_participant.perform_rpc(
                destination_identity=destination_identity,
                method=method,
                payload=payload,
            )
            self._logger.debug(
                f"[EventBridge] RPC '{method}' to '{destination_identity}' "
                f"returned: {response[:100]}..."
                if len(response) > 100
                else f"[EventBridge] RPC '{method}' to '{destination_identity}' "
                f"returned: {response}"
            )
            return response

        except asyncio.TimeoutError:
            self._logger.warning(
                f"RPC '{method}' to '{destination_identity}' timed out after {timeout}s"
            )
            return None
        except Exception as e:
            self._logger.error(
                f"RPC '{method}' to '{destination_identity}' failed: {e}"
            )
            return None

    def register_rpc_method(
        self,
        method: str,
        handler: Callable,
    ) -> bool:
        """
        Register an RPC method handler.

        Use this to handle incoming RPC calls from the frontend.

        Args:
            method: RPC method name to handle
            handler: Async function(data: RpcInvocationData) -> str

        Returns:
            True if registered successfully

        Example:
            async def handle_user_action(data):
                payload = json.loads(data.payload)
                # Process action...
                return json.dumps({"status": "ok"})

            bridge.register_rpc_method("userAction", handle_user_action)
        """
        if not self.local_participant:
            self._logger.warning("Cannot register RPC: no local participant")
            return False

        try:
            self.local_participant.register_rpc_method(method)(handler)
            self._logger.info(f"[EventBridge] Registered RPC method: {method}")
            return True
        except Exception as e:
            self._logger.error(f"Failed to register RPC method '{method}': {e}")
            return False

    async def request_location(
        self,
        destination_identity: str,
        reason: str = "find nearby places",
        timeout: float = 30.0,
    ) -> Optional[Dict[str, Any]]:
        """
        Request location from a participant via RPC.

        Sends a getLocation RPC to the frontend, which should trigger
        the browser's geolocation API and return coordinates.

        Args:
            destination_identity: Identity of the user participant
            reason: Human-readable reason for requesting location
            timeout: Timeout in seconds (default 30s for user interaction)

        Returns:
            Dict with latitude, longitude, accuracy, or None on error/timeout

        Example:
            location = await bridge.request_location(
                destination_identity="user-123",
                reason="find nearby restaurants"
            )
            if location:
                lat = location["latitude"]
                lng = location["longitude"]
        """
        payload = json.dumps(
            {
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
            }
        )

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
                    f"Location request denied: {result.get('error', 'unknown')}"
                )
                return None
        except json.JSONDecodeError:
            self._logger.error(f"Invalid location response: {response}")
            return None

    # =========================================================================
    # Event Listeners
    # =========================================================================

    def on_state_change(self, callback: Callable):
        """
        Register a callback for state change events.

        Args:
            callback: Function(state: str, source: str) to call on state change
        """
        self._state_listeners.append(callback)

    def on_transcript(self, callback: Callable):
        """
        Register a callback for transcript events.

        Args:
            callback: Function(event: TranscriptEvent) to call on transcript
        """
        self._transcript_listeners.append(callback)

    def remove_state_listener(self, callback: Callable):
        """Remove a state change listener."""
        if callback in self._state_listeners:
            self._state_listeners.remove(callback)

    def remove_transcript_listener(self, callback: Callable):
        """Remove a transcript listener."""
        if callback in self._transcript_listeners:
            self._transcript_listeners.remove(callback)

    def on_data_received(self, callback: Callable):
        """
        Register a callback for all data received events.

        The callback will receive a DataReceivedEvent dict with:
        - topic: The topic the data was sent on
        - data: Parsed JSON data (empty dict if not JSON)
        - participant_identity: Identity of sender
        - participant_name: Name of sender
        - raw_data: Raw bytes received

        Args:
            callback: Function(event: DataReceivedEvent) to call on data received

        Example:
            def handle_data(event):
                print(f"Got data from {event['participant_identity']}: {event['data']}")

            bridge.on_data_received(handle_data)
        """
        self._data_listeners.append(callback)

    def on_topic(self, topic: str, callback: Callable):
        """
        Register a callback for data received on a specific topic.

        Args:
            topic: Topic name to listen for
            callback: Function(event: DataReceivedEvent) to call

        Example:
            async def handle_user_action(event):
                action = event['data'].get('action')
                if action == 'select_provider':
                    provider_id = event['data'].get('provider_id')
                    await process_selection(provider_id)

            bridge.on_topic("user_action", handle_user_action)
        """
        if topic not in self._topic_listeners:
            self._topic_listeners[topic] = []
        self._topic_listeners[topic].append(callback)

    def remove_data_listener(self, callback: Callable):
        """Remove a global data listener."""
        if callback in self._data_listeners:
            self._data_listeners.remove(callback)

    def remove_topic_listener(self, topic: str, callback: Callable):
        """Remove a topic-specific listener."""
        if topic in self._topic_listeners and callback in self._topic_listeners[topic]:
            self._topic_listeners[topic].remove(callback)
            if not self._topic_listeners[topic]:
                del self._topic_listeners[topic]

    # =========================================================================
    # Convenience Methods for Common State Transitions
    # =========================================================================

    async def listening(self):
        """Set agent state to listening."""
        await self.set_agent_state(AgentState.LISTENING)

    async def thinking(self):
        """Set agent state to thinking."""
        await self.set_agent_state(AgentState.THINKING)

    async def speaking(self):
        """Set agent state to speaking."""
        await self.set_agent_state(AgentState.SPEAKING)

    async def initializing(self):
        """Set agent state to initializing."""
        await self.set_agent_state(AgentState.INITIALIZING)

    # =========================================================================
    # Conversation Management
    # =========================================================================

    def get_conversation(self) -> List[Dict]:
        """Get the full conversation history."""
        return [
            {
                "id": item.id,
                "role": item.role,
                "content": item.content,
                "timestamp": item.timestamp,
            }
            for item in self._conversation_items
        ]

    def clear_conversation(self):
        """Clear the conversation history."""
        self._conversation_items.clear()
        self._transcript_id = 0

    # =========================================================================
    # Metadata
    # =========================================================================

    async def set_agent_metadata(self, metadata: Dict[str, Any]):
        """
        Set agent metadata on the participant.

        Args:
            metadata: Dictionary of metadata to set
        """
        await self._ensure_initialized()

        if self.local_participant:
            try:
                await self.local_participant.set_metadata(json.dumps(metadata))
            except Exception as e:
                self._logger.error(f"Failed to set metadata: {e}")

    async def set_agent_attributes(self, attributes: Dict[str, str]):
        """
        Set agent attributes on the participant.

        Args:
            attributes: Dictionary of attributes to set
        """
        await self._ensure_initialized()

        if self.local_participant:
            try:
                await self.local_participant.set_attributes(attributes)
            except Exception as e:
                self._logger.error(f"Failed to set attributes: {e}")


# Global singleton for easy access
_global_bridge: Optional[LiveKitEventBridge] = None


def get_event_bridge() -> LiveKitEventBridge:
    """
    Get the global LiveKit event bridge instance.

    Returns:
        Global LiveKitEventBridge singleton
    """
    global _global_bridge
    if _global_bridge is None:
        _global_bridge = LiveKitEventBridge()
    return _global_bridge


def create_event_bridge(
    logger: Optional[logging.Logger] = None,
    emit_transcripts: bool = True,
) -> LiveKitEventBridge:
    """
    Create a new LiveKit event bridge instance.

    Args:
        logger: Optional logger
        emit_transcripts: Whether to emit transcript events

    Returns:
        New LiveKitEventBridge instance
    """
    return LiveKitEventBridge(
        logger=logger,
        emit_transcripts=emit_transcripts,
    )
