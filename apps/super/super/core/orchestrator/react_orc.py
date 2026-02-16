"""
ReActOrc - ReAct Orchestrator using LangGraph.

Implements a ReAct (Reason-Act-Observe) agent using LangGraph's
StateGraph for execution flow management.
"""

import logging
from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    TypedDict,
)

if TYPE_CHECKING:
    from super.core.orchestrator.three_layer.shared_context import SharedContext

from langgraph.graph import END, StateGraph

from super.core.handler.react_handler import ActionType, Observation, Thought
from super.core.logging import logging as app_logging
from super.core.orchestrator.base import BaseOrc
from super.core.tools import BaseTool, ToolRegistry, ToolResult

logger = app_logging.get_logger("orchestrator.react")


class AgentState(TypedDict):
    """State maintained across the ReAct graph execution."""

    objective: str
    messages: List[Dict[str, Any]]
    thoughts: List[Dict[str, Any]]
    observations: List[Dict[str, Any]]
    tool_calls: List[Dict[str, Any]]
    iteration: int
    max_iterations: int
    final_response: Optional[str]
    should_continue: bool
    metadata: Dict[str, Any]


@dataclass
class ReActConfig:
    """Configuration for ReActOrc."""

    max_iterations: int = 10
    thinking_callback: Optional[Callable[[Thought], None]] = None
    observation_callback: Optional[Callable[[Observation], None]] = None
    tool_call_callback: Optional[Callable[[str, Dict[str, Any], ToolResult], None]] = (
        None
    )


class ReActOrc(BaseOrc):
    """
    ReAct Orchestrator using LangGraph for execution flow.

    The orchestrator manages:
    - Tool registration and execution
    - ReAct loop (think -> act -> observe)
    - State management across iterations
    - Callbacks for observability

    The LangGraph StateGraph handles:
    - Node execution (think, act, observe)
    - Conditional routing based on action type
    - State persistence across steps
    """

    def __init__(
        self,
        config: Optional[ReActConfig] = None,
        tool_registry: Optional[ToolRegistry] = None,
        think_fn: Optional[Callable[[AgentState], Thought]] = None,
        logger_instance: logging.Logger = logging.getLogger(__name__),
        **kwargs: Any,
    ) -> None:
        super().__init__(logger=logger_instance, **kwargs)
        self._config = config or ReActConfig()
        self._tool_registry = tool_registry or ToolRegistry()
        self._think_fn = think_fn
        self._graph: Optional[StateGraph] = None
        self._shared_context: Optional["SharedContext"] = None

    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool with the orchestrator."""
        self._tool_registry.register(tool)

    def register_tools(self, tools: List[BaseTool]) -> None:
        """Register multiple tools."""
        for tool in tools:
            self._tool_registry.register(tool)

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get schemas for all registered tools."""
        return self._tool_registry.get_all_schemas()

    def set_think_fn(self, fn: Callable[[AgentState], Thought]) -> None:
        """Set the thinking function (typically LLM-based)."""
        self._think_fn = fn

    def _create_initial_state(
        self, objective: str, **kwargs: Any
    ) -> AgentState:
        """Create initial state for graph execution."""
        return AgentState(
            objective=objective,
            messages=[{"role": "user", "content": objective}],
            thoughts=[],
            observations=[],
            tool_calls=[],
            iteration=0,
            max_iterations=self._config.max_iterations,
            final_response=None,
            should_continue=True,
            metadata=kwargs,
        )

    def _think_node(self, state: AgentState) -> AgentState:
        """
        Think node: Reason about the current state.

        Uses the configured think_fn or a default implementation.
        """
        if state["iteration"] >= state["max_iterations"]:
            thought = Thought(
                reasoning="Max iterations reached",
                next_action=ActionType.RESPOND,
                response_content="Task completed after maximum iterations.",
            )
        elif self._think_fn:
            thought = self._think_fn(state)
        else:
            thought = self._default_think(state)

        thought_dict = {
            "reasoning": thought.reasoning,
            "action": thought.next_action.value,
            "tool_name": thought.tool_name,
            "tool_params": thought.tool_params,
            "response_content": thought.response_content,
        }

        state["thoughts"].append(thought_dict)
        state["iteration"] += 1

        if self._config.thinking_callback:
            self._config.thinking_callback(thought)

        return state

    def _default_think(self, state: AgentState) -> Thought:
        """Default thinking logic when no think_fn is provided."""
        tools = self._tool_registry.list_tools()

        if not tools:
            return Thought(
                reasoning=f"No tools available. Responding to: {state['objective']}",
                next_action=ActionType.RESPOND,
                response_content=f"Received: {state['objective']}",
            )

        if state["observations"]:
            last_obs = state["observations"][-1]
            if last_obs.get("success"):
                return Thought(
                    reasoning="Previous action succeeded, providing response",
                    next_action=ActionType.RESPOND,
                    response_content=f"Result: {last_obs.get('data')}",
                )

        return Thought(
            reasoning=f"Processing objective: {state['objective']}",
            next_action=ActionType.RESPOND,
            response_content="Default response - configure think_fn for custom logic",
        )

    async def _act_node(self, state: AgentState) -> AgentState:
        """
        Act node: Execute the decided action.

        Handles tool calls, responses, and other action types.
        """
        if not state["thoughts"]:
            return state

        last_thought = state["thoughts"][-1]
        action = ActionType(last_thought["action"])

        if action == ActionType.TOOL_CALL:
            tool_name = last_thought.get("tool_name")
            tool_params = last_thought.get("tool_params", {})

            if tool_name:
                result = await self._tool_registry.execute(tool_name, **tool_params)

                state["tool_calls"].append(
                    {
                        "tool": tool_name,
                        "params": tool_params,
                        "success": result.success,
                        "data": result.data,
                        "error": result.error,
                    }
                )

                observation = Observation(
                    action_type=ActionType.TOOL_CALL,
                    success=result.success,
                    data=result.data,
                    error=result.error,
                    metadata={"tool": tool_name},
                )

                if self._config.tool_call_callback:
                    self._config.tool_call_callback(tool_name, tool_params, result)
            else:
                observation = Observation(
                    action_type=ActionType.TOOL_CALL,
                    success=False,
                    error="No tool name specified",
                )

        elif action == ActionType.RESPOND:
            observation = Observation(
                action_type=ActionType.RESPOND,
                success=True,
                data=last_thought.get("response_content"),
            )
            state["final_response"] = last_thought.get("response_content")
            state["should_continue"] = False

        elif action == ActionType.WAIT:
            observation = Observation(
                action_type=ActionType.WAIT,
                success=True,
                data="Waiting for input",
            )
            state["should_continue"] = False

        else:
            observation = Observation(
                action_type=action,
                success=False,
                error=f"Unknown action: {action}",
            )

        obs_dict = {
            "action_type": observation.action_type.value,
            "success": observation.success,
            "data": observation.data,
            "error": observation.error,
        }
        state["observations"].append(obs_dict)

        if self._config.observation_callback:
            self._config.observation_callback(observation)

        return state

    def _should_continue(self, state: AgentState) -> Literal["think", "end"]:
        """Determine if the ReAct loop should continue."""
        if not state["should_continue"]:
            return "end"
        if state["iteration"] >= state["max_iterations"]:
            return "end"
        if state["final_response"] is not None:
            return "end"
        return "think"

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph StateGraph for ReAct execution."""
        graph = StateGraph(AgentState)

        graph.add_node("think", self._think_node)
        graph.add_node("act", self._act_node)

        graph.set_entry_point("think")

        graph.add_edge("think", "act")

        graph.add_conditional_edges(
            "act",
            self._should_continue,
            {
                "think": "think",
                "end": END,
            },
        )

        return graph

    async def execute(
        self, objective: str, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Execute the ReAct loop for the given objective.

        Args:
            objective: The task/goal to accomplish
            **kwargs: Additional context

        Returns:
            Dict with execution results
        """
        state = self._create_initial_state(objective, **kwargs)
        graph = self._build_graph()
        compiled = graph.compile()

        final_state = state
        async for step in compiled.astream(state):
            for node_name, node_state in step.items():
                final_state = node_state

        return {
            "status": "success" if final_state.get("final_response") else "incomplete",
            "objective": objective,
            "final_response": final_state.get("final_response"),
            "iterations": final_state.get("iteration", 0),
            "thoughts": final_state.get("thoughts", []),
            "observations": final_state.get("observations", []),
            "tool_calls": final_state.get("tool_calls", []),
            "cost": self.total_cost,
        }

    async def _send_callback(self, message: Any) -> None:
        """Send callback message (for BaseOrc compatibility)."""
        pass

    def set_shared_context(self, context: "SharedContext") -> None:
        """Set the shared context for three-layer orchestration."""
        self._shared_context = context

    async def process_action(self, action_id: str) -> Optional[Dict[str, Any]]:
        """
        Process an action from the shared context.

        This is a best-effort processing method. On error, the action is
        cancelled and None is returned.

        Args:
            action_id: The ID of the action to process

        Returns:
            Dict with response and intent, or None if action not found/failed
        """
        if self._shared_context is None:
            return None

        action = self._shared_context.get_action(action_id)
        if action is None:
            return None

        # Lazy imports to avoid circular dependency
        from super.core.orchestrator.three_layer.classifier import classify_intent
        from super.core.orchestrator.three_layer.models import (
            ActionStatus,
            ExecutionMode,
        )

        try:
            input_text = action["input"]
            classification = classify_intent(input_text)

            await self._shared_context.set_mode(action_id, classification.mode)
            await self._shared_context.update_status(action_id, ActionStatus.PROCESSING)

            if classification.mode == ExecutionMode.ASYNC:
                engagement_msg = self._get_engagement_message(classification.intent.value)
                await self._shared_context.set_engagement(action_id, engagement_msg)

            result = await self.execute(input_text)

            response = result.get("final_response")
            if response is None:
                logger.warning(
                    "Incomplete execution for action %s: no final_response", action_id
                )
                response = ""

            await self._shared_context.complete_action(action_id, {"response": response})

            return {
                "response": response,
                "intent": classification.intent.value,
            }
        except Exception:
            logger.exception("Error processing action %s", action_id)
            await self._shared_context.update_status(action_id, ActionStatus.CANCELLED)
            return None

    def _get_engagement_message(self, intent: str) -> str:
        """Get an engagement message for async processing."""
        messages = {
            "provider_search": "I'm searching for providers that match your criteria...",
            "booking": "I'm working on scheduling that appointment for you...",
            "phone_call": "I'm preparing to make that call for you...",
            "research": "I'm researching that information for you...",
        }
        return messages.get(intent, "I'm working on that for you...")

    def __repr__(self) -> str:
        tool_count = len(self._tool_registry)
        return f"ReActOrc(tools={tool_count}, max_iter={self._config.max_iterations})"
