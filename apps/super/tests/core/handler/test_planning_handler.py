"""Tests for PlanningHandler."""

from typing import Any, Dict

import pytest

from super.core.handler.planning_handler import (
    Plan,
    PlanningContext,
    PlanningHandler,
    PlanStep,
    StepStatus,
)
from super.core.handler.react_handler import ActionType
from super.core.tools import BaseTool, ToolCategory, ToolResult


class MultiplyTool(BaseTool):
    """Tool that multiplies two numbers."""

    name = "multiply"
    description = "Multiply two numbers"
    category = ToolCategory.UTILITY

    async def execute(self, a: int = 1, b: int = 1) -> ToolResult:
        return ToolResult(success=True, data={"result": a * b})

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "parameters": {"type": "object", "properties": {}},
        }


class TestPlanStep:
    """Tests for PlanStep."""

    def test_step_creation(self) -> None:
        step = PlanStep(
            step_id="step_1",
            description="Search for data",
            tool="search",
            tool_params={"query": "test"},
        )
        assert step.step_id == "step_1"
        assert step.status == StepStatus.PENDING

    def test_step_to_dict(self) -> None:
        step = PlanStep(
            step_id="step_1",
            description="Test step",
            status=StepStatus.COMPLETED,
            result="Done",
        )
        d = step.to_dict()
        assert d["step_id"] == "step_1"
        assert d["status"] == "completed"
        assert d["result"] == "Done"


class TestPlan:
    """Tests for Plan."""

    def test_plan_creation(self) -> None:
        plan = Plan(objective="Complete task")
        assert plan.objective == "Complete task"
        assert len(plan.steps) == 0
        assert plan.is_complete is False

    def test_add_step(self) -> None:
        plan = Plan(objective="Test")
        step = plan.add_step(description="First step", tool="search")
        assert step.step_id == "step_1"
        assert len(plan.steps) == 1

    def test_add_multiple_steps(self) -> None:
        plan = Plan(objective="Test")
        plan.add_step(description="Step 1")
        plan.add_step(description="Step 2")
        plan.add_step(description="Step 3")
        assert len(plan.steps) == 3
        assert plan.steps[2].step_id == "step_3"

    def test_get_current_step(self) -> None:
        plan = Plan(objective="Test")
        plan.add_step(description="First")
        plan.add_step(description="Second")
        current = plan.get_current_step()
        assert current.description == "First"

    def test_advance(self) -> None:
        plan = Plan(objective="Test")
        plan.add_step(description="First")
        plan.add_step(description="Second")
        next_step = plan.advance()
        assert next_step.description == "Second"
        assert plan.current_step_index == 1

    def test_advance_to_completion(self) -> None:
        plan = Plan(objective="Test")
        plan.add_step(description="Only step")
        plan.advance()
        assert plan.is_complete is True
        assert plan.get_current_step() is None

    def test_get_pending_steps(self) -> None:
        plan = Plan(objective="Test")
        plan.add_step(description="Step 1")
        plan.add_step(description="Step 2")
        plan.steps[0].status = StepStatus.COMPLETED
        pending = plan.get_pending_steps()
        assert len(pending) == 1
        assert pending[0].description == "Step 2"

    def test_get_completed_steps(self) -> None:
        plan = Plan(objective="Test")
        plan.add_step(description="Step 1")
        plan.add_step(description="Step 2")
        plan.steps[0].status = StepStatus.COMPLETED
        completed = plan.get_completed_steps()
        assert len(completed) == 1

    def test_to_dict(self) -> None:
        plan = Plan(objective="Test")
        plan.add_step(description="Step 1")
        d = plan.to_dict()
        assert d["objective"] == "Test"
        assert len(d["steps"]) == 1
        assert d["progress"] == "0/1"


class TestPlanningContext:
    """Tests for PlanningContext."""

    def test_context_with_plan(self) -> None:
        plan = Plan(objective="Test")
        plan.add_step(description="Step 1")
        ctx = PlanningContext(objective="Test", plan=plan)
        assert ctx.plan is not None
        assert len(ctx.plan.steps) == 1

    def test_to_dict_with_plan(self) -> None:
        plan = Plan(objective="Test")
        ctx = PlanningContext(objective="Test", plan=plan)
        d = ctx.to_dict()
        assert "plan" in d


class TestPlanningHandler:
    """Tests for PlanningHandler."""

    def test_handler_init(self) -> None:
        handler = PlanningHandler()
        assert handler.name == "planning_handler"
        assert handler._max_iterations == 20

    @pytest.mark.anyio
    async def test_create_plan(self) -> None:
        handler = PlanningHandler()
        plan = await handler.create_plan("Complete the task")
        assert plan.objective == "Complete the task"
        assert len(plan.steps) >= 1

    @pytest.mark.anyio
    async def test_create_plan_with_tools(self) -> None:
        handler = PlanningHandler()
        handler.register_tool(MultiplyTool())
        plan = await handler.create_plan("Multiply numbers")
        assert len(plan.steps) >= 1
        assert plan.steps[0].tool == "multiply"

    @pytest.mark.anyio
    async def test_execute_step_with_tool(self) -> None:
        handler = PlanningHandler()
        handler.register_tool(MultiplyTool())
        step = PlanStep(
            step_id="step_1",
            description="Multiply 3 and 4",
            tool="multiply",
            tool_params={"a": 3, "b": 4},
        )
        obs = await handler.execute_step(step)
        assert obs.success is True
        assert obs.data == {"result": 12}
        assert step.status == StepStatus.COMPLETED

    @pytest.mark.anyio
    async def test_execute_step_without_tool(self) -> None:
        handler = PlanningHandler()
        step = PlanStep(
            step_id="step_1",
            description="Just a response step",
        )
        obs = await handler.execute_step(step)
        assert obs.success is True
        assert obs.action_type == ActionType.RESPOND
        assert step.status == StepStatus.COMPLETED

    @pytest.mark.anyio
    async def test_execute_step_failure(self) -> None:
        handler = PlanningHandler()
        step = PlanStep(
            step_id="step_1",
            description="Call nonexistent tool",
            tool="nonexistent",
        )
        obs = await handler.execute_step(step)
        assert obs.success is False
        assert step.status == StepStatus.FAILED

    @pytest.mark.anyio
    async def test_think_no_plan(self) -> None:
        handler = PlanningHandler()
        ctx = PlanningContext(objective="Test", plan=None)
        thought = await handler.think(ctx)
        assert thought.next_action == ActionType.WAIT

    @pytest.mark.anyio
    async def test_think_plan_complete(self) -> None:
        handler = PlanningHandler()
        plan = Plan(objective="Test")
        plan.add_step(description="Only step")
        plan.steps[0].status = StepStatus.COMPLETED
        plan.is_complete = True
        ctx = PlanningContext(objective="Test", plan=plan)
        thought = await handler.think(ctx)
        assert thought.next_action == ActionType.RESPOND

    @pytest.mark.anyio
    async def test_execute_full_plan(self) -> None:
        handler = PlanningHandler(max_iterations=10)
        handler.register_tool(MultiplyTool())
        result = await handler.execute("Calculate something")
        assert "objective" in result
        assert "plan" in result
        assert result["plan"]["is_complete"] is True

    def test_repr(self) -> None:
        handler = PlanningHandler(max_iterations=15)
        handler.register_tool(MultiplyTool())
        assert "tools=1" in repr(handler)
        assert "max_iter=15" in repr(handler)

    def test_dump(self) -> None:
        handler = PlanningHandler(max_iterations=25)
        dump = handler.dump
        assert dump["name"] == "planning_handler"
        assert dump["max_iterations"] == 25
