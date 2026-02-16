"""Tests for three-layer events."""

import pytest
from typing import Any, Dict, List

from super.core.orchestrator.three_layer.events import (
    EventType,
    Event,
    EventEmitter,
    create_event,
)


class TestEventType:
    """Tests for EventType enum."""

    def test_all_event_types_defined(self) -> None:
        types = [e.value for e in EventType]
        assert "status_changed" in types
        assert "action_completed" in types
        assert "waiting_for_input" in types
        assert "plan_created" in types


class TestEvent:
    """Tests for Event creation."""

    def test_create_status_changed_event(self) -> None:
        event = create_event(
            event_type=EventType.STATUS_CHANGED,
            action_id="a1",
            data={"old_status": "pending", "new_status": "processing"}
        )
        assert event["type"] == EventType.STATUS_CHANGED
        assert event["action_id"] == "a1"
        assert event["data"]["new_status"] == "processing"


class TestEventEmitter:
    """Tests for EventEmitter."""

    @pytest.fixture
    def emitter(self) -> EventEmitter:
        return EventEmitter()

    @pytest.mark.anyio
    async def test_emit_to_multiple_subscribers(
        self, emitter: EventEmitter
    ) -> None:
        results: List[str] = []

        async def handler1(event: Event) -> None:
            results.append("h1")

        async def handler2(event: Event) -> None:
            results.append("h2")

        emitter.subscribe(EventType.ACTION_COMPLETED, handler1)
        emitter.subscribe(EventType.ACTION_COMPLETED, handler2)

        event = create_event(
            event_type=EventType.ACTION_COMPLETED,
            action_id="a1",
            data={}
        )
        await emitter.emit(event)

        assert "h1" in results
        assert "h2" in results

    @pytest.mark.anyio
    async def test_unsubscribe(self, emitter: EventEmitter) -> None:
        call_count = 0

        async def handler(event: Event) -> None:
            nonlocal call_count
            call_count += 1

        emitter.subscribe(EventType.STATUS_CHANGED, handler)
        emitter.unsubscribe(EventType.STATUS_CHANGED, handler)

        event = create_event(
            event_type=EventType.STATUS_CHANGED,
            action_id="a1",
            data={}
        )
        await emitter.emit(event)

        assert call_count == 0
