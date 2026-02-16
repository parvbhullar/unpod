"""Event system for three-layer orchestration."""

import asyncio
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, TypedDict


class EventType(Enum):
    """Types of events emitted by shared context."""

    STATUS_CHANGED = "status_changed"
    PLAN_CREATED = "plan_created"
    STEP_COMPLETED = "step_completed"
    PROGRESS_UPDATE = "progress_update"
    WAITING_FOR_INPUT = "waiting_for_input"
    USER_RESPONSE = "user_response"
    CALL_INITIATED = "call_initiated"
    CALL_STATUS_UPDATE = "call_status_update"
    CALL_COMPLETED = "call_completed"
    ACTION_COMPLETED = "action_completed"
    ACTION_CANCELLED = "action_cancelled"


class Event(TypedDict):
    """An event in the system."""

    type: EventType
    action_id: str
    data: Dict[str, Any]
    timestamp: str


def create_event(
    event_type: EventType,
    action_id: str,
    data: Dict[str, Any],
) -> Event:
    """Create a new event."""
    return Event(
        type=event_type,
        action_id=action_id,
        data=data,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


EventHandler = Callable[[Event], Awaitable[None]]


class EventEmitter:
    """Async event emitter for the three-layer system."""

    def __init__(self) -> None:
        self._handlers: Dict[EventType, List[EventHandler]] = {}

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Subscribe a handler to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Unsubscribe a handler from an event type."""
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h != handler
            ]

    async def emit(self, event: Event) -> None:
        """Emit an event to all subscribers."""
        handlers = self._handlers.get(event["type"], [])
        await asyncio.gather(*[h(event) for h in handlers])
