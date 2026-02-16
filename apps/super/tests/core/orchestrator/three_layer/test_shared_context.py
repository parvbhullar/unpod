"""Tests for SharedContext."""

import pytest
from typing import List

from super.core.orchestrator.three_layer.shared_context import SharedContext
from super.core.orchestrator.three_layer.models import (
    ActionStatus,
    ExecutionMode,
)
from super.core.orchestrator.three_layer.events import Event, EventType


class TestSharedContext:
    """Tests for SharedContext."""

    @pytest.fixture
    def context(self) -> SharedContext:
        return SharedContext()

    @pytest.mark.anyio
    async def test_create_action(self, context: SharedContext) -> None:
        action = await context.create_action(
            thread_id="t1",
            input_text="Hello"
        )
        assert action["thread_id"] == "t1"
        assert action["input"] == "Hello"
        assert action["status"] == ActionStatus.PENDING
        assert action["action_id"].startswith("act_")

    @pytest.mark.anyio
    async def test_get_action(self, context: SharedContext) -> None:
        created = await context.create_action(thread_id="t1", input_text="Hello")
        retrieved = context.get_action(created["action_id"])
        assert retrieved == created

    @pytest.mark.anyio
    async def test_get_nonexistent_action_returns_none(
        self, context: SharedContext
    ) -> None:
        assert context.get_action("nonexistent") is None

    @pytest.mark.anyio
    async def test_update_status_emits_event(self, context: SharedContext) -> None:
        events: List[Event] = []

        async def capture(event: Event) -> None:
            events.append(event)

        context.subscribe(EventType.STATUS_CHANGED, capture)

        action = await context.create_action(thread_id="t1", input_text="Test")
        await context.update_status(
            action["action_id"],
            ActionStatus.PROCESSING
        )

        assert len(events) == 1
        assert events[0]["type"] == EventType.STATUS_CHANGED
        assert events[0]["data"]["new_status"] == ActionStatus.PROCESSING

    @pytest.mark.anyio
    async def test_set_mode(self, context: SharedContext) -> None:
        action = await context.create_action(thread_id="t1", input_text="Search")
        await context.set_mode(action["action_id"], ExecutionMode.ASYNC)

        updated = context.get_action(action["action_id"])
        assert updated is not None
        assert updated["mode"] == ExecutionMode.ASYNC

    @pytest.mark.anyio
    async def test_set_engagement(self, context: SharedContext) -> None:
        action = await context.create_action(thread_id="t1", input_text="Search")
        await context.set_engagement(action["action_id"], "Looking for results...")

        updated = context.get_action(action["action_id"])
        assert updated is not None
        assert updated["engagement"] == "Looking for results..."

    @pytest.mark.anyio
    async def test_complete_action_emits_event(self, context: SharedContext) -> None:
        events: List[Event] = []

        async def capture(event: Event) -> None:
            events.append(event)

        context.subscribe(EventType.ACTION_COMPLETED, capture)

        action = await context.create_action(thread_id="t1", input_text="Test")
        await context.complete_action(
            action["action_id"],
            result={"response": "Done!"}
        )

        completed_events = [e for e in events if e["type"] == EventType.ACTION_COMPLETED]
        assert len(completed_events) == 1
        assert completed_events[0]["data"]["result"]["response"] == "Done!"

    @pytest.mark.anyio
    async def test_cancel_action(self, context: SharedContext) -> None:
        events: List[Event] = []

        async def capture(event: Event) -> None:
            events.append(event)

        context.subscribe(EventType.ACTION_CANCELLED, capture)

        action = await context.create_action(thread_id="t1", input_text="Search")
        await context.cancel_action(action["action_id"], reason="User interrupted")

        cancelled = context.get_action(action["action_id"])
        assert cancelled is not None
        assert cancelled["status"] == ActionStatus.CANCELLED

        cancel_events = [e for e in events if e["type"] == EventType.ACTION_CANCELLED]
        assert len(cancel_events) == 1

    @pytest.mark.anyio
    async def test_get_pending_actions(self, context: SharedContext) -> None:
        await context.create_action(thread_id="t1", input_text="First")
        action2 = await context.create_action(thread_id="t1", input_text="Second")
        await context.update_status(action2["action_id"], ActionStatus.PROCESSING)

        pending = context.get_pending_actions(thread_id="t1")
        assert len(pending) == 1
        assert pending[0]["input"] == "First"
