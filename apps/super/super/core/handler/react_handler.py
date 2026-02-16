"""
ReActHandler - Handler implementing Reason-Act-Observe loop.

Extends ToolCallHandler to provide the ReAct (Reasoning and Acting)
pattern for agentic behavior. The handler reasons about the task,
decides on actions, executes tools, and observes results.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from super.core.handler.tool_handler import ToolCallHandler
from super.core.logging import logging as app_logging
from super.core.tools import ToolRegistry, ToolResult

logger = app_logging.get_logger("handler.react")


class ActionType(str, Enum):
    """Types of actions the handler can take."""

    TOOL_CALL = "tool_call"
    RESPOND = "respond"
    WAIT = "wait"
    DELEGATE = "delegate"


@dataclass
class Thought:
    """Represents the handler's reasoning about a situation."""

    reasoning: str
    next_action: ActionType
    tool_name: Optional[str] = None
    tool_params: Dict[str, Any] = field(default_factory=dict)
    response_content: Optional[str] = None
    confidence: float = 1.0


@dataclass
class Observation:
    """Result of an action, used to inform next reasoning step."""

    action_type: ActionType
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReActContext:
    """Context maintained across ReAct iterations."""

    objective: str
    files: List[Dict[str, Any]] = field(default_factory=list)
    thoughts: List[Thought] = field(default_factory=list)
    observations: List[Observation] = field(default_factory=list)
    iteration: int = 0
    max_iterations: int = 10
    should_continue: bool = True
    final_response: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_thought(self, thought: Thought) -> None:
        self.thoughts.append(thought)

    def add_observation(self, observation: Observation) -> None:
        self.observations.append(observation)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "objective": self.objective,
            "iteration": self.iteration,
            "thought_count": len(self.thoughts),
            "observation_count": len(self.observations),
            "should_continue": self.should_continue,
            "final_response": self.final_response,
        }


class ReActHandler(ToolCallHandler):
    """
    Handler implementing the ReAct (Reason-Act-Observe) pattern.

    The ReAct loop:
    1. Think: Reason about the current state and decide next action
    2. Act: Execute the decided action (tool call or response)
    3. Observe: Process the result and update context
    4. Repeat until task is complete or max iterations reached
    """

    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        max_iterations: int = 10,
        **kwargs: Any,
    ) -> None:
        super().__init__(tool_registry=tool_registry, **kwargs)
        self._max_iterations = max_iterations

    @property
    def name(self) -> str:
        return "react_handler"

    @property
    def dump(self) -> Dict[str, Any]:
        base_dump = super().dump
        base_dump.update(
            {
                "name": self.name,
                "max_iterations": self._max_iterations,
            }
        )
        return base_dump

    def __repr__(self) -> str:
        tool_count = len(self._tool_registry)
        return f"ReActHandler(tools={tool_count}, max_iter={self._max_iterations})"

    async def think(self, context: ReActContext) -> Thought:
        """
        Reason about the current state and decide next action.

        This is a placeholder that should be overridden with LLM-based
        reasoning in concrete implementations.

        Args:
            context: Current ReAct context

        Returns:
            Thought with reasoning and decided action
        """
        if context.iteration >= context.max_iterations:
            return Thought(
                reasoning="Max iterations reached, generating final response",
                next_action=ActionType.RESPOND,
                response_content="Task completed after maximum iterations.",
            )

        if not self._tool_registry.list_tools():
            return Thought(
                reasoning="No tools available, responding directly",
                next_action=ActionType.RESPOND,
                response_content=f"Received objective: {context.objective}",
            )

        return Thought(
            reasoning=f"Processing objective: {context.objective}",
            next_action=ActionType.RESPOND,
            response_content="Default response - override think() for custom logic",
        )

    async def act(self, thought: Thought) -> Observation:
        """
        Execute the action decided in the think step.

        Args:
            thought: The thought containing the action to take

        Returns:
            Observation with action result
        """
        if thought.next_action == ActionType.TOOL_CALL:
            if not thought.tool_name:
                return Observation(
                    action_type=ActionType.TOOL_CALL,
                    success=False,
                    error="No tool name specified",
                )

            result = await self.call_tool(thought.tool_name, **thought.tool_params)

            return Observation(
                action_type=ActionType.TOOL_CALL,
                success=result.success,
                data=result.data,
                error=result.error,
                metadata={"tool": thought.tool_name, "params": thought.tool_params},
            )

        elif thought.next_action == ActionType.RESPOND:
            return Observation(
                action_type=ActionType.RESPOND,
                success=True,
                data=thought.response_content,
            )

        elif thought.next_action == ActionType.WAIT:
            return Observation(
                action_type=ActionType.WAIT,
                success=True,
                data="Waiting for external input",
            )

        elif thought.next_action == ActionType.DELEGATE:
            return Observation(
                action_type=ActionType.DELEGATE,
                success=True,
                data="Delegation requested",
            )

        return Observation(
            action_type=thought.next_action,
            success=False,
            error=f"Unknown action type: {thought.next_action}",
        )

    def observe(self, observation: Observation, context: ReActContext) -> ReActContext:
        """
        Process action result and update context.

        Args:
            observation: Result of the action
            context: Current context

        Returns:
            Updated context
        """
        context.add_observation(observation)
        context.iteration += 1

        if observation.action_type == ActionType.RESPOND:
            context.should_continue = False
            context.final_response = observation.data

        elif not observation.success:
            logger.warning(f"Action failed: {observation.error}")

        if context.iteration >= context.max_iterations:
            context.should_continue = False
            if not context.final_response:
                context.final_response = "Max iterations reached"

        return context

    def should_continue(self, context: ReActContext) -> bool:
        """Check if the ReAct loop should continue."""
        return context.should_continue and context.iteration < context.max_iterations

    async def execute(
        self,
        objective: str,
        files: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Execute the ReAct loop for the given objective.

        Args:
            objective: The task/goal to accomplish
            files: Optional list of file context
            **kwargs: Additional context

        Returns:
            Dict with execution result including final response
        """
        context = ReActContext(
            objective=objective,
            files=files or [],
            max_iterations=self._max_iterations,
            metadata=kwargs,
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
            "thoughts": [
                {"reasoning": t.reasoning, "action": t.next_action.value}
                for t in context.thoughts
            ],
            "tool_calls": self.get_tool_call_history(),
        }
