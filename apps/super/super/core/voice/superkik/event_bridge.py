"""
Event bridge for superkik to LiveKit voice integration.

Maps superkik events to LiveKit voice output (TTS) and data channels,
enabling real-time voice feedback during agentic processing.

Supports both:
- Legacy ThreadEvents from superkik-py SDK (subprocess-based)
- Native PyEvent from superkik bindings (PyO3-based)
"""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from super.core.voice.superkik.handler import SuperKikHandler

# Import superkik event types (legacy SDK)
try:
    from superkik import (
        AgentMessageDeltaEvent,
        AgentMessageEvent,
        AgentReasoningDeltaEvent,
        AgentReasoningEvent,
        ErrorEvent,
        TaskCompleteEvent,
        TaskStartedEvent,
        ThreadEvent,
        ToolCallBeginEvent,
        ToolCallEndEvent,
        WarningEvent,
    )

    SUPERKIK_SDK_AVAILABLE = True
except ImportError:
    SUPERKIK_SDK_AVAILABLE = False
    ThreadEvent = Any  # type: ignore

# Import native bindings event type
try:
    from superkik._native import Event as NativeEvent

    SUPERKIK_NATIVE_AVAILABLE = True
except ImportError:
    SUPERKIK_NATIVE_AVAILABLE = False
    NativeEvent = Any  # type: ignore

# Topic for chat messages
TOPIC_LK_CHAT = "lk.chat"
TOPIC_SUPERKIK_STATUS = "superkik.status"


class SuperkikEventBridge:
    """
    Bridge superkik events to LiveKit voice system.

    Handles:
    - Agent message streaming → TTS synthesis
    - Tool call events → Status updates to frontend
    - Error events → Error handling and recovery
    - Reasoning events → Optional debug output
    """

    def __init__(
        self,
        handler: "SuperKikHandler",
        logger: Optional[logging.Logger] = None,
    ):
        self._handler = handler
        self._logger = logger or logging.getLogger("superkik.event_bridge")

        # TTS buffering for natural speech
        self._tts_buffer = ""
        self._min_tts_chunk = 50  # Minimum chars before flushing to TTS
        self._sentence_endings = (".", "!", "?", ":", ";")

        # Message correlation
        self._current_message_id: Optional[str] = None
        self._current_turn_id: Optional[int] = None

        # Tool tracking
        self._active_tools: Dict[str, str] = {}  # call_id -> tool_name

    async def process_event(self, event: ThreadEvent) -> None:
        """
        Route legacy SDK event to appropriate handler.

        Args:
            event: ThreadEvent from superkik-py SDK
        """
        if not SUPERKIK_SDK_AVAILABLE:
            self._logger.warning("superkik SDK not available, cannot process events")
            return

        event_type = event.type

        try:
            if event_type == "task_started":
                await self._handle_task_started(event)
            elif event_type == "task_complete":
                await self._handle_task_complete(event)
            elif event_type == "agent_message_delta":
                await self._handle_message_delta(event)
            elif event_type == "agent_message":
                await self._handle_message_complete(event)
            elif event_type == "agent_reasoning_delta":
                await self._handle_reasoning_delta(event)
            elif event_type == "agent_reasoning":
                await self._handle_reasoning_complete(event)
            elif event_type == "tool_call_begin":
                await self._handle_tool_begin(event)
            elif event_type == "tool_call_end":
                await self._handle_tool_end(event)
            elif event_type == "error":
                await self._handle_error(event)
            elif event_type == "warning":
                await self._handle_warning(event)
            else:
                self._logger.debug(f"Unhandled event type: {event_type}")

        except Exception as e:
            self._logger.error(f"Error processing event {event_type}: {e}")

    async def process_native_event(self, event: "NativeEvent") -> None:
        """
        Route native PyO3 event to appropriate handler.

        Args:
            event: Event from superkik native bindings
        """
        if not SUPERKIK_NATIVE_AVAILABLE:
            self._logger.warning("superkik native bindings not available")
            return

        event_type = event.event_type
        event_data = event.as_dict()
        data = event_data.get("data", {})

        try:
            if event_type == "task_started":
                await self._handle_native_task_started(data)
            elif event_type == "task_complete":
                await self._handle_native_task_complete(data)
            elif event_type == "agent_message_delta":
                await self._handle_native_message_delta(data)
            elif event_type == "agent_message":
                await self._handle_native_message_complete(data)
            elif event_type == "agent_reasoning_delta":
                await self._handle_native_reasoning_delta(data)
            elif event_type == "agent_reasoning":
                await self._handle_native_reasoning_complete(data)
            elif event_type == "tool_call_begin":
                await self._handle_native_tool_begin(data)
            elif event_type == "tool_call_end":
                await self._handle_native_tool_end(data)
            elif event_type == "error":
                await self._handle_native_error(data)
            elif event_type == "warning":
                await self._handle_native_warning(data)
            else:
                self._logger.debug(f"Unhandled native event type: {event_type}")

        except Exception as e:
            self._logger.error(f"Error processing native event {event_type}: {e}")

    async def _handle_task_started(self, event: TaskStartedEvent) -> None:
        """Handle task/turn started event."""
        self._current_turn_id = event.turn_id
        self._current_message_id = str(uuid.uuid4())
        self._tts_buffer = ""

        self._logger.debug(f"Task started: turn_id={event.turn_id}")

        # Notify frontend of processing start
        await self._publish_status("processing", {"turn_id": event.turn_id})

    async def _handle_task_complete(self, event: TaskCompleteEvent) -> None:
        """Handle task/turn completed event."""
        # Flush any remaining TTS buffer
        if self._tts_buffer:
            await self._flush_tts()

        self._logger.debug(f"Task complete: turn_id={event.turn_id}")

        # Notify frontend of completion
        await self._publish_status("complete", {"turn_id": event.turn_id})

        # Reset state
        self._current_turn_id = None
        self._current_message_id = None
        self._tts_buffer = ""

    async def _handle_message_delta(self, event: AgentMessageDeltaEvent) -> None:
        """Handle streaming message delta."""
        delta = event.delta
        self._tts_buffer += delta

        # Check if we should flush to TTS
        if self._should_flush_tts():
            await self._flush_tts()

    async def _handle_message_complete(self, event: AgentMessageEvent) -> None:
        """Handle complete agent message."""
        message = event.message

        # Flush any buffered content first
        if self._tts_buffer:
            await self._flush_tts()

        # Publish complete message to data channel
        await self._publish_chat_message(message)

        self._logger.debug(f"Message complete: {len(message)} chars")

    async def _handle_reasoning_delta(
        self, event: AgentReasoningDeltaEvent
    ) -> None:
        """Handle streaming reasoning delta (optional debug output)."""
        # Reasoning is not spoken - just log for debugging
        self._logger.debug(f"Reasoning: {event.delta[:50]}...")

    async def _handle_reasoning_complete(self, event: AgentReasoningEvent) -> None:
        """Handle complete reasoning (optional debug output)."""
        self._logger.debug(f"Reasoning complete: {len(event.reasoning)} chars")

    async def _handle_tool_begin(self, event: ToolCallBeginEvent) -> None:
        """Handle tool call started."""
        call_id = event.call_id
        tool_name = event.name
        args = event.args or {}

        self._active_tools[call_id] = tool_name
        self._logger.info(f"Tool started: {tool_name} (call_id={call_id})")

        # Notify frontend of tool execution
        await self._publish_status(
            "tool_running",
            {
                "call_id": call_id,
                "tool": tool_name,
                "args": args,
            },
        )

    async def _handle_tool_end(self, event: ToolCallEndEvent) -> None:
        """Handle tool call completed."""
        call_id = event.call_id
        tool_name = self._active_tools.pop(call_id, "unknown")
        success = event.success
        output = event.output

        self._logger.info(
            f"Tool completed: {tool_name} (success={success}, call_id={call_id})"
        )

        # Notify frontend of tool completion
        await self._publish_status(
            "tool_complete" if success else "tool_error",
            {
                "call_id": call_id,
                "tool": tool_name,
                "success": success,
                "output": output[:200] if output else None,
            },
        )

    async def _handle_error(self, event: ErrorEvent) -> None:
        """Handle error event."""
        message = event.message
        code = getattr(event, "code", None)

        self._logger.error(f"Superkik error: {message} (code={code})")

        # Notify frontend of error
        await self._publish_status(
            "error",
            {
                "message": message,
                "code": code,
            },
        )

        # Speak error to user
        await self._speak_error(message)

    async def _handle_warning(self, event: WarningEvent) -> None:
        """Handle warning event."""
        message = event.message
        self._logger.warning(f"Superkik warning: {message}")

    def _should_flush_tts(self) -> bool:
        """Determine if TTS buffer should be flushed."""
        if not self._tts_buffer:
            return False

        # Flush on sentence endings
        if self._tts_buffer.rstrip().endswith(self._sentence_endings):
            return len(self._tts_buffer) >= self._min_tts_chunk

        # Flush on large buffer
        if len(self._tts_buffer) >= self._min_tts_chunk * 3:
            return True

        return False

    async def _flush_tts(self) -> None:
        """Flush TTS buffer to speech synthesis."""
        if not self._tts_buffer.strip():
            self._tts_buffer = ""
            return

        text = self._tts_buffer.strip()
        self._tts_buffer = ""

        try:
            # Use handler's session for TTS
            session = getattr(self._handler, "_session", None)
            if session:
                await session.say(text, allow_interruptions=True)
                self._logger.debug(f"TTS: {text[:50]}...")
            else:
                self._logger.warning("No session available for TTS")
        except Exception as e:
            self._logger.error(f"TTS failed: {e}")

    async def _publish_chat_message(self, message: str) -> None:
        """Publish complete message to data channel."""
        message_id = self._current_message_id or str(uuid.uuid4())

        data = {
            "type": "message",
            "id": message_id,
            "role": "assistant",
            "content": message,
            "source": "superkik",
        }

        try:
            event_bridge = getattr(self._handler, "_event_bridge", None)
            if event_bridge:
                await event_bridge.publish_data(data, topic=TOPIC_LK_CHAT)
                self._logger.debug(f"Published message to {TOPIC_LK_CHAT}")
        except Exception as e:
            self._logger.error(f"Failed to publish message: {e}")

    async def _publish_status(self, status: str, data: Dict[str, Any]) -> None:
        """Publish status update to data channel."""
        payload = {
            "type": "status",
            "status": status,
            "turn_id": self._current_turn_id,
            **data,
        }

        try:
            event_bridge = getattr(self._handler, "_event_bridge", None)
            if event_bridge:
                await event_bridge.publish_data(payload, topic=TOPIC_SUPERKIK_STATUS)
        except Exception as e:
            self._logger.error(f"Failed to publish status: {e}")

    async def _speak_error(self, message: str) -> None:
        """Speak error message to user."""
        error_response = f"I encountered an error: {message}"

        try:
            session = getattr(self._handler, "_session", None)
            if session:
                await session.say(error_response, allow_interruptions=True)
        except Exception as e:
            self._logger.error(f"Failed to speak error: {e}")

    # Native event handlers (for PyO3 bindings)

    async def _handle_native_task_started(self, data: Dict[str, Any]) -> None:
        """Handle native task/turn started event."""
        turn_id = data.get("turn_id")
        self._current_turn_id = turn_id
        self._current_message_id = str(uuid.uuid4())
        self._tts_buffer = ""

        self._logger.debug(f"Task started: turn_id={turn_id}")
        await self._publish_status("processing", {"turn_id": turn_id})

    async def _handle_native_task_complete(self, data: Dict[str, Any]) -> None:
        """Handle native task/turn completed event."""
        if self._tts_buffer:
            await self._flush_tts()

        turn_id = data.get("turn_id")
        self._logger.debug(f"Task complete: turn_id={turn_id}")
        await self._publish_status("complete", {"turn_id": turn_id})

        self._current_turn_id = None
        self._current_message_id = None
        self._tts_buffer = ""

    async def _handle_native_message_delta(self, data: Dict[str, Any]) -> None:
        """Handle native streaming message delta."""
        delta = data.get("delta", "")
        self._tts_buffer += delta

        if self._should_flush_tts():
            await self._flush_tts()

    async def _handle_native_message_complete(self, data: Dict[str, Any]) -> None:
        """Handle native complete agent message."""
        message = data.get("message", "")

        if self._tts_buffer:
            await self._flush_tts()

        await self._publish_chat_message(message)
        self._logger.debug(f"Message complete: {len(message)} chars")

    async def _handle_native_reasoning_delta(self, data: Dict[str, Any]) -> None:
        """Handle native streaming reasoning delta."""
        delta = data.get("delta", "")
        self._logger.debug(f"Reasoning: {delta[:50]}...")

    async def _handle_native_reasoning_complete(self, data: Dict[str, Any]) -> None:
        """Handle native complete reasoning."""
        reasoning = data.get("reasoning", "")
        self._logger.debug(f"Reasoning complete: {len(reasoning)} chars")

    async def _handle_native_tool_begin(self, data: Dict[str, Any]) -> None:
        """Handle native tool call started."""
        call_id = data.get("call_id", "")
        tool_name = data.get("name", "")
        args = data.get("args", {})

        self._active_tools[call_id] = tool_name
        self._logger.info(f"Tool started: {tool_name} (call_id={call_id})")

        await self._publish_status(
            "tool_running",
            {"call_id": call_id, "tool": tool_name, "args": args},
        )

    async def _handle_native_tool_end(self, data: Dict[str, Any]) -> None:
        """Handle native tool call completed."""
        call_id = data.get("call_id", "")
        tool_name = self._active_tools.pop(call_id, "unknown")
        success = data.get("success", True)
        output = data.get("output", "")

        self._logger.info(
            f"Tool completed: {tool_name} (success={success}, call_id={call_id})"
        )

        await self._publish_status(
            "tool_complete" if success else "tool_error",
            {
                "call_id": call_id,
                "tool": tool_name,
                "success": success,
                "output": output[:200] if output else None,
            },
        )

    async def _handle_native_error(self, data: Dict[str, Any]) -> None:
        """Handle native error event."""
        message = data.get("message", "Unknown error")
        code = data.get("code")

        self._logger.error(f"Superkik error: {message} (code={code})")
        await self._publish_status("error", {"message": message, "code": code})
        await self._speak_error(message)

    async def _handle_native_warning(self, data: Dict[str, Any]) -> None:
        """Handle native warning event."""
        message = data.get("message", "")
        self._logger.warning(f"Superkik warning: {message}")

    def reset(self) -> None:
        """Reset bridge state for new session."""
        self._tts_buffer = ""
        self._current_message_id = None
        self._current_turn_id = None
        self._active_tools.clear()
