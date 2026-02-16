"""End-to-end integration tests for three-layer architecture.

These tests verify the full flow through SharedContext and ReActOrc
without requiring the full LiveKit handler.
"""

import pytest


class TestEndToEndFlow:
    """Test the end-to-end integration flow."""

    @pytest.fixture
    def context(self):
        """Create SharedContext with event subscriptions."""
        from super.core.orchestrator.three_layer.shared_context import SharedContext

        return SharedContext()

    @pytest.fixture
    def orc(self, context):
        """Create ReActOrc connected to SharedContext."""
        from super.core.orchestrator.react_orc import ReActOrc

        orc = ReActOrc()
        orc.set_shared_context(context)
        return orc

    @pytest.mark.anyio
    async def test_full_sync_flow(self, context, orc) -> None:
        """Test full SYNC flow: greeting input -> response."""
        from super.core.orchestrator.three_layer.events import EventType
        from super.core.orchestrator.three_layer.models import ActionStatus

        delivered = []

        # Subscribe to completion events
        async def on_complete(event):
            result = event.get("data", {}).get("result", {})
            response = result.get("response")
            if response:
                delivered.append(response)

        context.subscribe(EventType.ACTION_COMPLETED, on_complete)

        # Create action (simulates user input)
        action = await context.create_action(
            thread_id="test_thread",
            input_text="Hello!",
        )
        action_id = action["action_id"]

        # Process through ReActOrc (simulates PA processing)
        result = await orc.process_action(action_id)

        # Verify flow completed correctly
        assert result is not None
        assert "response" in result
        final_action = context.get_action(action_id)
        assert final_action["status"] == ActionStatus.DONE

    @pytest.mark.anyio
    async def test_full_async_flow_with_engagement(self, context, orc) -> None:
        """Test full ASYNC flow: search input -> engagement -> response."""
        from super.core.orchestrator.three_layer.events import EventType
        from super.core.orchestrator.three_layer.models import ExecutionMode

        engagements = []

        # Subscribe to status changes for engagement
        async def on_status(event):
            action_id = event.get("action_id")
            if not action_id:
                return
            action = context.get_action(action_id)
            if action and action.get("engagement"):
                engagements.append(action["engagement"])

        context.subscribe(EventType.STATUS_CHANGED, on_status)

        # Create action (simulates user input)
        action = await context.create_action(
            thread_id="test_thread",
            input_text="Find me a dentist",
        )
        action_id = action["action_id"]

        # Process through ReActOrc
        result = await orc.process_action(action_id)

        # Verify ASYNC flow with engagement
        assert result is not None
        final_action = context.get_action(action_id)
        assert final_action["mode"] == ExecutionMode.ASYNC
        assert final_action["engagement"] is not None
        assert len(engagements) > 0

    @pytest.mark.anyio
    async def test_error_handling_cancels_action(self, context) -> None:
        """Test that errors during processing cancel the action."""
        from super.core.orchestrator.react_orc import ReActOrc
        from super.core.orchestrator.three_layer.models import ActionStatus

        orc = ReActOrc()
        orc.set_shared_context(context)

        # Create action
        action = await context.create_action(
            thread_id="test_thread",
            input_text="Test input",
        )
        action_id = action["action_id"]

        # Corrupt the action to trigger error path
        # (removing required field to simulate processing error)
        context._actions[action_id]["input"] = None  # type: ignore

        # Process - should handle error gracefully
        result = await orc.process_action(action_id)

        # Error should result in cancelled status
        assert result is None
        final_action = context.get_action(action_id)
        assert final_action["status"] == ActionStatus.CANCELLED

    @pytest.mark.anyio
    async def test_multiple_threads_independent(self, context, orc) -> None:
        """Test that different threads don't interfere."""
        from super.core.orchestrator.three_layer.models import ActionStatus

        # Create actions in different threads
        action1 = await context.create_action(
            thread_id="thread_1",
            input_text="Hello",
        )
        action2 = await context.create_action(
            thread_id="thread_2",
            input_text="Hi there",
        )

        # Process both
        result1 = await orc.process_action(action1["action_id"])
        result2 = await orc.process_action(action2["action_id"])

        # Both should complete independently
        assert result1 is not None
        assert result2 is not None
        assert action1["action_id"] != action2["action_id"]
        assert context.get_action(action1["action_id"])["status"] == ActionStatus.DONE
        assert context.get_action(action2["action_id"])["status"] == ActionStatus.DONE


class TestTwoTierClassification:
    """Test two-tier classification (local response vs PA routing)."""

    @pytest.mark.parametrize(
        "input_text,expect_sync",
        [
            ("Hello", True),
            ("Hi there", True),
            ("Thanks", True),
            ("Yes", True),
            ("Find a dentist", False),
            ("Book an appointment", False),
            ("Search for doctors", False),
        ],
    )
    @pytest.mark.anyio
    async def test_intent_classification_determines_mode(
        self, input_text: str, expect_sync: bool
    ) -> None:
        """Test that intent classification correctly sets execution mode."""
        from super.core.orchestrator.three_layer.classifier import classify_intent
        from super.core.orchestrator.three_layer.models import ExecutionMode

        result = classify_intent(input_text)

        if expect_sync:
            assert result.mode == ExecutionMode.SYNC
        else:
            assert result.mode == ExecutionMode.ASYNC
