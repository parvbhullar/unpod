"""Shared context (observation layer) for three-layer orchestration."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from super.core.orchestrator.three_layer.events import (
    Event,
    EventEmitter,
    EventHandler,
    EventType,
    create_event,
)
from super.core.orchestrator.three_layer.models import (
    ActionState,
    ActionStatus,
    ExecutionMode,
    create_action_state,
)


@runtime_checkable
class PersistenceAdapter(Protocol):
    """Protocol for persistence adapters.

    Implementations handle storage of ActionState to external systems (e.g., databases).
    """

    async def save_action(self, action: ActionState) -> None:
        """Save action to persistent storage (upsert - handles create and update)."""
        ...

    async def load_action(self, action_id: str) -> Optional[ActionState]:
        """Load action from persistent storage by ID."""
        ...

    async def load_thread_actions(self, thread_id: str) -> List[ActionState]:
        """Load all actions for a thread from persistent storage."""
        ...


class SharedContext:
    """
    Shared context layer for three-layer orchestration.

    Holds action state, emits events on changes, no logic.
    CA and PA both read/write through this interface.
    """

    def __init__(
        self,
        persistence: Optional[PersistenceAdapter] = None,
    ) -> None:
        self._actions: Dict[str, ActionState] = {}
        self._emitter = EventEmitter()
        self._persistence = persistence

    async def _persist(self, action: ActionState) -> None:
        """Save action to persistence if configured."""
        if self._persistence is not None:
            await self._persistence.save_action(action)

    async def load_thread_state(self, thread_id: str) -> None:
        """Load actions from persistence and replace in-memory cache.

        Used for session restart scenarios where we need to restore state.
        """
        if self._persistence is None:
            return

        actions = await self._persistence.load_thread_actions(thread_id)
        self._actions = {action["action_id"]: action for action in actions}

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Subscribe to events."""
        self._emitter.subscribe(event_type, handler)

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Unsubscribe from events."""
        self._emitter.unsubscribe(event_type, handler)

    def _generate_action_id(self) -> str:
        """Generate a unique action ID."""
        return f"act_{uuid.uuid4().hex[:8]}"

    async def create_action(
        self,
        thread_id: str,
        input_text: str,
        supersedes: Optional[str] = None,
    ) -> ActionState:
        """Create a new action in pending state."""
        action_id = self._generate_action_id()
        action = create_action_state(
            action_id=action_id,
            thread_id=thread_id,
            input_text=input_text,
            supersedes=supersedes,
        )
        self._actions[action_id] = action
        await self._persist(action)
        return action

    def get_action(self, action_id: str) -> Optional[ActionState]:
        """Get an action by ID."""
        return self._actions.get(action_id)

    def get_pending_actions(self, thread_id: str) -> List[ActionState]:
        """Get all pending actions for a thread."""
        return [
            a for a in self._actions.values()
            if a["thread_id"] == thread_id and a["status"] == ActionStatus.PENDING
        ]

    def get_active_action(self, thread_id: str) -> Optional[ActionState]:
        """Get the currently processing action for a thread."""
        for action in self._actions.values():
            if (
                action["thread_id"] == thread_id
                and action["status"] in (ActionStatus.PROCESSING, ActionStatus.WAITING)
            ):
                return action
        return None

    async def update_status(
        self,
        action_id: str,
        new_status: ActionStatus,
    ) -> None:
        """Update action status and emit event."""
        action = self._actions.get(action_id)
        if not action:
            return

        old_status = action["status"]
        action["status"] = new_status
        action["updated_at"] = datetime.now(timezone.utc).isoformat()

        await self._persist(action)

        event = create_event(
            event_type=EventType.STATUS_CHANGED,
            action_id=action_id,
            data={"old_status": old_status, "new_status": new_status},
        )
        await self._emitter.emit(event)

    async def set_mode(
        self,
        action_id: str,
        mode: ExecutionMode,
    ) -> None:
        """Set execution mode for an action."""
        action = self._actions.get(action_id)
        if action:
            action["mode"] = mode
            action["updated_at"] = datetime.now(timezone.utc).isoformat()

    async def set_engagement(
        self,
        action_id: str,
        engagement: str,
    ) -> None:
        """Set engagement message for ASYNC actions."""
        action = self._actions.get(action_id)
        if action:
            action["engagement"] = engagement
            action["updated_at"] = datetime.now(timezone.utc).isoformat()

    async def set_waiting(
        self,
        action_id: str,
        waiting_for: str,
        prompt: Optional[str] = None,
    ) -> None:
        """Set action to waiting state."""
        action = self._actions.get(action_id)
        if not action:
            return

        action["waiting_for"] = waiting_for
        await self.update_status(action_id, ActionStatus.WAITING)

        event = create_event(
            event_type=EventType.WAITING_FOR_INPUT,
            action_id=action_id,
            data={"waiting_for": waiting_for, "prompt": prompt},
        )
        await self._emitter.emit(event)

    async def resolve_waiting(
        self,
        action_id: str,
        input_data: Dict[str, Any],
    ) -> None:
        """Resolve waiting state with user input."""
        action = self._actions.get(action_id)
        if not action:
            return

        action["waiting_for"] = None
        await self.update_status(action_id, ActionStatus.PROCESSING)

        event = create_event(
            event_type=EventType.USER_RESPONSE,
            action_id=action_id,
            data={"input": input_data},
        )
        await self._emitter.emit(event)

    async def complete_action(
        self,
        action_id: str,
        result: Dict[str, Any],
    ) -> None:
        """Complete an action with result."""
        action = self._actions.get(action_id)
        if not action:
            return

        action["result"] = result
        await self.update_status(action_id, ActionStatus.DONE)

        event = create_event(
            event_type=EventType.ACTION_COMPLETED,
            action_id=action_id,
            data={"result": result},
        )
        await self._emitter.emit(event)

    async def cancel_action(
        self,
        action_id: str,
        reason: str,
    ) -> None:
        """Cancel an action."""
        action = self._actions.get(action_id)
        if not action:
            return

        await self.update_status(action_id, ActionStatus.CANCELLED)

        event = create_event(
            event_type=EventType.ACTION_CANCELLED,
            action_id=action_id,
            data={"reason": reason},
        )
        await self._emitter.emit(event)
