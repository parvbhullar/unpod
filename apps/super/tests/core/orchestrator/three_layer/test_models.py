"""Tests for three-layer models."""

import pytest
from datetime import datetime

from super.core.orchestrator.three_layer.models import (
    ActionStatus,
    ExecutionMode,
    ActionState,
    PlanStep,
    PlanState,
    create_action_state,
)


class TestActionStatus:
    """Tests for ActionStatus enum."""

    def test_all_statuses_defined(self) -> None:
        statuses = [s.value for s in ActionStatus]
        assert "pending" in statuses
        assert "processing" in statuses
        assert "waiting" in statuses
        assert "done" in statuses
        assert "cancelled" in statuses


class TestExecutionMode:
    """Tests for ExecutionMode enum."""

    def test_modes_defined(self) -> None:
        assert ExecutionMode.SYNC.value == "sync"
        assert ExecutionMode.ASYNC.value == "async"


class TestActionState:
    """Tests for ActionState."""

    def test_create_action_state_minimal(self) -> None:
        state = create_action_state(
            action_id="a1",
            thread_id="t1",
            input_text="Hello"
        )
        assert state["action_id"] == "a1"
        assert state["thread_id"] == "t1"
        assert state["input"] == "Hello"
        assert state["status"] == ActionStatus.PENDING
        assert state["mode"] is None

    def test_create_action_state_with_mode(self) -> None:
        state = create_action_state(
            action_id="a2",
            thread_id="t1",
            input_text="Search dentists",
            mode=ExecutionMode.ASYNC
        )
        assert state["mode"] == ExecutionMode.ASYNC

    def test_action_state_has_timestamps(self) -> None:
        state = create_action_state(
            action_id="a3",
            thread_id="t1",
            input_text="Test"
        )
        assert "created_at" in state
        assert "updated_at" in state


class TestPlanState:
    """Tests for PlanState."""

    def test_plan_step_creation(self) -> None:
        step = PlanStep(
            step_id="s1",
            name="Verify provider",
            status="pending",
            input=None,
            result=None
        )
        assert step["step_id"] == "s1"
        assert step["status"] == "pending"
