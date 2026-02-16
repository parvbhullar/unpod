"""Tests for ReActOrc SharedContext integration."""

import pytest
from typing import Any, Dict

from super.core.orchestrator.react_orc import ReActOrc
from super.core.orchestrator.three_layer.shared_context import SharedContext
from super.core.orchestrator.three_layer.models import (
    ActionStatus,
    ExecutionMode,
)


class TestSetSharedContext:
    """Tests for set_shared_context method."""

    def test_set_shared_context_sets_context(self) -> None:
        """Verify set_shared_context stores the context."""
        orc = ReActOrc()
        context = SharedContext()

        orc.set_shared_context(context)

        assert orc._shared_context is context

    def test_shared_context_initially_none(self) -> None:
        """Verify _shared_context is None by default."""
        orc = ReActOrc()

        assert orc._shared_context is None


class TestProcessAction:
    """Tests for process_action method."""

    @pytest.fixture
    def orc(self) -> ReActOrc:
        """Create a ReActOrc instance."""
        return ReActOrc()

    @pytest.fixture
    def context(self) -> SharedContext:
        """Create a SharedContext instance."""
        return SharedContext()

    @pytest.mark.anyio
    async def test_process_action_returns_none_without_context(
        self, orc: ReActOrc
    ) -> None:
        """Verify process_action returns None if no shared context is set."""
        result = await orc.process_action("nonexistent")

        assert result is None

    @pytest.mark.anyio
    async def test_process_action_returns_none_for_nonexistent_action(
        self, orc: ReActOrc, context: SharedContext
    ) -> None:
        """Verify process_action returns None for action not in context."""
        orc.set_shared_context(context)

        result = await orc.process_action("nonexistent_action_id")

        assert result is None

    @pytest.mark.anyio
    async def test_process_action_updates_status_to_done(
        self, orc: ReActOrc, context: SharedContext
    ) -> None:
        """Verify process_action updates status to DONE on completion."""
        orc.set_shared_context(context)
        action = await context.create_action(
            thread_id="thread_1",
            input_text="Hello world",
        )
        action_id = action["action_id"]

        await orc.process_action(action_id)

        updated_action = context.get_action(action_id)
        assert updated_action is not None
        assert updated_action["status"] == ActionStatus.DONE

    @pytest.mark.anyio
    async def test_process_action_sets_mode(
        self, orc: ReActOrc, context: SharedContext
    ) -> None:
        """Verify process_action sets execution mode from classification."""
        orc.set_shared_context(context)
        action = await context.create_action(
            thread_id="thread_1",
            input_text="Find a doctor near me",
        )
        action_id = action["action_id"]

        await orc.process_action(action_id)

        updated_action = context.get_action(action_id)
        assert updated_action is not None
        assert updated_action["mode"] == ExecutionMode.ASYNC

    @pytest.mark.anyio
    async def test_process_action_sets_sync_mode_for_greeting(
        self, orc: ReActOrc, context: SharedContext
    ) -> None:
        """Verify process_action sets SYNC mode for greetings."""
        orc.set_shared_context(context)
        action = await context.create_action(
            thread_id="thread_1",
            input_text="Hello there!",
        )
        action_id = action["action_id"]

        await orc.process_action(action_id)

        updated_action = context.get_action(action_id)
        assert updated_action is not None
        assert updated_action["mode"] == ExecutionMode.SYNC

    @pytest.mark.anyio
    async def test_process_action_returns_response_dict(
        self, orc: ReActOrc, context: SharedContext
    ) -> None:
        """Verify process_action returns dict with response and intent."""
        orc.set_shared_context(context)
        action = await context.create_action(
            thread_id="thread_1",
            input_text="Hello",
        )
        action_id = action["action_id"]

        result = await orc.process_action(action_id)

        assert result is not None
        assert "response" in result
        assert "intent" in result

    @pytest.mark.anyio
    async def test_process_action_sets_engagement_for_async(
        self, orc: ReActOrc, context: SharedContext
    ) -> None:
        """Verify process_action sets engagement message for ASYNC mode."""
        orc.set_shared_context(context)
        action = await context.create_action(
            thread_id="thread_1",
            input_text="Book an appointment",
        )
        action_id = action["action_id"]

        await orc.process_action(action_id)

        updated_action = context.get_action(action_id)
        assert updated_action is not None
        assert updated_action["engagement"] is not None


class TestGetEngagementMessage:
    """Tests for _get_engagement_message helper."""

    def test_get_engagement_message_returns_string(self) -> None:
        """Verify _get_engagement_message returns a string."""
        orc = ReActOrc()

        message = orc._get_engagement_message("booking")

        assert isinstance(message, str)
        assert len(message) > 0

    def test_get_engagement_message_default_for_unknown(self) -> None:
        """Verify _get_engagement_message returns default for unknown intent."""
        orc = ReActOrc()

        message = orc._get_engagement_message("unknown_intent_xyz")

        assert isinstance(message, str)
        assert len(message) > 0
