"""
PlanningHandler - Handler with planning capabilities.

Extends ReActHandler to add multi-step planning. The handler can
break down complex objectives into steps and execute them.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from super.core.handler.react_handler import (
    ActionType,
    Observation,
    ReActContext,
    ReActHandler,
    Thought,
)
from super.core.logging import logging as app_logging
from super.core.tools import ToolRegistry

logger = app_logging.get_logger("handler.planning")


class StepStatus(str, Enum):
    """Status of a plan step."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    """A single step in a plan."""

    step_id: str
    description: str
    tool: Optional[str] = None
    tool_params: Dict[str, Any] = field(default_factory=dict)
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "description": self.description,
            "tool": self.tool,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
        }


@dataclass
class Plan:
    """A multi-step plan for accomplishing an objective."""

    objective: str
    steps: List[PlanStep] = field(default_factory=list)
    current_step_index: int = 0
    is_complete: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_step(
        self,
        description: str,
        tool: Optional[str] = None,
        tool_params: Optional[Dict[str, Any]] = None,
        dependencies: Optional[List[str]] = None,
    ) -> PlanStep:
        step_id = f"step_{len(self.steps) + 1}"
        step = PlanStep(
            step_id=step_id,
            description=description,
            tool=tool,
            tool_params=tool_params or {},
            dependencies=dependencies or [],
        )
        self.steps.append(step)
        return step

    def get_current_step(self) -> Optional[PlanStep]:
        if self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    def advance(self) -> Optional[PlanStep]:
        self.current_step_index += 1
        if self.current_step_index >= len(self.steps):
            self.is_complete = True
            return None
        return self.get_current_step()

    def get_pending_steps(self) -> List[PlanStep]:
        return [s for s in self.steps if s.status == StepStatus.PENDING]

    def get_completed_steps(self) -> List[PlanStep]:
        return [s for s in self.steps if s.status == StepStatus.COMPLETED]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "objective": self.objective,
            "steps": [s.to_dict() for s in self.steps],
            "current_step_index": self.current_step_index,
            "is_complete": self.is_complete,
            "progress": f"{len(self.get_completed_steps())}/{len(self.steps)}",
        }


@dataclass
class PlanningContext(ReActContext):
    """Extended context with planning information."""

    plan: Optional[Plan] = None

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        if self.plan:
            base["plan"] = self.plan.to_dict()
        return base


class PlanningHandler(ReActHandler):
    """
    Handler that can create and execute multi-step plans.

    Extends ReActHandler with:
    - Plan creation from objectives
    - Step-by-step execution
    - Progress tracking
    """

    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        max_iterations: int = 20,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            tool_registry=tool_registry, max_iterations=max_iterations, **kwargs
        )

    @property
    def name(self) -> str:
        return "planning_handler"

    @property
    def dump(self) -> Dict[str, Any]:
        base_dump = super().dump
        base_dump["name"] = self.name
        return base_dump

    def __repr__(self) -> str:
        tool_count = len(self._tool_registry)
        return f"PlanningHandler(tools={tool_count}, max_iter={self._max_iterations})"

    async def create_plan(self, objective: str) -> Plan:
        """
        Create a plan from an objective.

        This is a placeholder that returns a simple single-step plan.
        Override with LLM-based planning in concrete implementations.

        Args:
            objective: The goal to plan for

        Returns:
            Plan with steps to accomplish the objective
        """
        plan = Plan(objective=objective)

        tools = self._tool_registry.list_tools()
        if tools:
            plan.add_step(
                description=f"Use available tools to accomplish: {objective}",
                tool=tools[0] if tools else None,
            )
        else:
            plan.add_step(
                description=f"Respond to objective: {objective}",
            )

        return plan

    async def execute_step(self, step: PlanStep) -> Observation:
        """
        Execute a single plan step.

        Args:
            step: The step to execute

        Returns:
            Observation with step result
        """
        step.status = StepStatus.IN_PROGRESS

        if step.tool:
            result = await self.call_tool(step.tool, **step.tool_params)
            if result.success:
                step.status = StepStatus.COMPLETED
                step.result = result.data
                return Observation(
                    action_type=ActionType.TOOL_CALL,
                    success=True,
                    data=result.data,
                    metadata={"step_id": step.step_id, "tool": step.tool},
                )
            else:
                step.status = StepStatus.FAILED
                step.error = result.error
                return Observation(
                    action_type=ActionType.TOOL_CALL,
                    success=False,
                    error=result.error,
                    metadata={"step_id": step.step_id, "tool": step.tool},
                )
        else:
            step.status = StepStatus.COMPLETED
            step.result = step.description
            return Observation(
                action_type=ActionType.RESPOND,
                success=True,
                data=step.description,
                metadata={"step_id": step.step_id},
            )

    async def think(self, context: ReActContext) -> Thought:
        """
        Think about the current planning state.

        Args:
            context: Current context (should be PlanningContext)

        Returns:
            Thought about next action
        """
        if not isinstance(context, PlanningContext):
            return await super().think(context)

        if context.plan is None:
            return Thought(
                reasoning="No plan exists, need to create one",
                next_action=ActionType.WAIT,
            )

        current_step = context.plan.get_current_step()
        if current_step is None or context.plan.is_complete:
            completed = context.plan.get_completed_steps()
            return Thought(
                reasoning=f"Plan complete with {len(completed)} steps executed",
                next_action=ActionType.RESPOND,
                response_content=self._summarize_plan_results(context.plan),
            )

        if current_step.tool:
            return Thought(
                reasoning=f"Executing step: {current_step.description}",
                next_action=ActionType.TOOL_CALL,
                tool_name=current_step.tool,
                tool_params=current_step.tool_params,
            )
        else:
            return Thought(
                reasoning=f"Processing step: {current_step.description}",
                next_action=ActionType.RESPOND,
                response_content=current_step.description,
            )

    def _summarize_plan_results(self, plan: Plan) -> str:
        """Create a summary of plan execution results."""
        completed = plan.get_completed_steps()
        failed = [s for s in plan.steps if s.status == StepStatus.FAILED]

        summary_parts = [f"Completed {len(completed)}/{len(plan.steps)} steps."]

        if failed:
            summary_parts.append(f"Failed steps: {len(failed)}")

        for step in completed:
            if step.result:
                summary_parts.append(f"- {step.description}: {step.result}")

        return " ".join(summary_parts)

    def observe(self, observation: Observation, context: ReActContext) -> ReActContext:
        """
        Observe action result and update planning context.

        Args:
            observation: Result of the action
            context: Current context

        Returns:
            Updated context
        """
        context = super().observe(observation, context)

        if isinstance(context, PlanningContext) and context.plan:
            if observation.success and observation.action_type in (
                ActionType.TOOL_CALL,
                ActionType.RESPOND,
            ):
                context.plan.advance()

            if context.plan.is_complete:
                context.should_continue = False
                if not context.final_response:
                    context.final_response = self._summarize_plan_results(context.plan)

        return context

    async def execute(
        self,
        objective: str,
        files: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Execute the planning handler for an objective.

        Creates a plan and executes it step by step.

        Args:
            objective: The task/goal to accomplish
            files: Optional file context
            **kwargs: Additional context

        Returns:
            Dict with execution result and plan details
        """
        plan = await self.create_plan(objective)

        context = PlanningContext(
            objective=objective,
            files=files or [],
            max_iterations=self._max_iterations,
            metadata=kwargs,
            plan=plan,
        )

        while self.should_continue(context):
            thought = await self.think(context)
            context.add_thought(thought)

            observation = await self.act(thought)
            context = self.observe(observation, context)

        return {
            "objective": objective,
            "final_response": context.final_response,
            "iterations": context.iteration,
            "plan": context.plan.to_dict() if context.plan else None,
            "tool_calls": self.get_tool_call_history(),
        }
