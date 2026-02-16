"""Tests for ReActOrc."""

from typing import Any, Dict, List

import pytest

from super.core.handler.react_handler import ActionType, Thought
from super.core.orchestrator.react_orc import AgentState, ReActConfig, ReActOrc
from super.core.tools import BaseTool, ToolCategory, ToolResult


class CalculatorTool(BaseTool):
    """Simple calculator tool for testing."""

    name = "calculator"
    description = "Perform basic arithmetic"
    category = ToolCategory.UTILITY

    async def execute(
        self, operation: str = "add", a: int = 0, b: int = 0
    ) -> ToolResult:
        operations = {
            "add": a + b,
            "subtract": a - b,
            "multiply": a * b,
            "divide": a / b if b != 0 else 0,
        }
        result = operations.get(operation, 0)
        return ToolResult(success=True, data={"result": result})

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {"type": "string"},
                    "a": {"type": "integer"},
                    "b": {"type": "integer"},
                },
            },
        }


class FailingTool(BaseTool):
    """Tool that always fails."""

    name = "failing"
    description = "Always fails"
    category = ToolCategory.UTILITY

    async def execute(self, **kwargs: Any) -> ToolResult:
        return ToolResult(success=False, error="Intentional failure")

    def get_schema(self) -> Dict[str, Any]:
        return {"name": self.name, "parameters": {"type": "object", "properties": {}}}


class TestReActConfig:
    """Tests for ReActConfig."""

    def test_default_config(self) -> None:
        config = ReActConfig()
        assert config.max_iterations == 10
        assert config.thinking_callback is None

    def test_custom_config(self) -> None:
        callback_calls: List[Thought] = []

        def callback(t: Thought) -> None:
            callback_calls.append(t)

        config = ReActConfig(max_iterations=5, thinking_callback=callback)
        assert config.max_iterations == 5
        assert config.thinking_callback is callback


class TestReActOrc:
    """Tests for ReActOrc."""

    def test_orc_init(self) -> None:
        orc = ReActOrc()
        assert len(orc._tool_registry) == 0
        assert orc._config.max_iterations == 10

    def test_orc_with_config(self) -> None:
        config = ReActConfig(max_iterations=5)
        orc = ReActOrc(config=config)
        assert orc._config.max_iterations == 5

    def test_register_tool(self) -> None:
        orc = ReActOrc()
        orc.register_tool(CalculatorTool())
        assert "calculator" in orc._tool_registry

    def test_register_tools(self) -> None:
        orc = ReActOrc()
        orc.register_tools([CalculatorTool(), FailingTool()])
        assert len(orc._tool_registry) == 2

    def test_get_tool_schemas(self) -> None:
        orc = ReActOrc()
        orc.register_tool(CalculatorTool())
        schemas = orc.get_tool_schemas()
        assert len(schemas) == 1
        assert schemas[0]["name"] == "calculator"

    def test_create_initial_state(self) -> None:
        orc = ReActOrc()
        state = orc._create_initial_state("Test objective", extra="data")
        assert state["objective"] == "Test objective"
        assert state["iteration"] == 0
        assert state["should_continue"] is True
        assert state["metadata"]["extra"] == "data"

    def test_default_think_no_tools(self) -> None:
        orc = ReActOrc()
        state = orc._create_initial_state("Test")
        thought = orc._default_think(state)
        assert thought.next_action == ActionType.RESPOND

    def test_default_think_with_observations(self) -> None:
        orc = ReActOrc()
        orc.register_tool(CalculatorTool())
        state = orc._create_initial_state("Calculate 2+2")
        state["observations"].append(
            {"action_type": "tool_call", "success": True, "data": {"result": 4}}
        )
        thought = orc._default_think(state)
        assert thought.next_action == ActionType.RESPOND

    def test_think_node_increments_iteration(self) -> None:
        orc = ReActOrc()
        state = orc._create_initial_state("Test")
        assert state["iteration"] == 0
        updated = orc._think_node(state)
        assert updated["iteration"] == 1
        assert len(updated["thoughts"]) == 1

    def test_think_node_max_iterations(self) -> None:
        config = ReActConfig(max_iterations=3)
        orc = ReActOrc(config=config)
        state = orc._create_initial_state("Test")
        state["iteration"] = 3
        state["max_iterations"] = 3
        updated = orc._think_node(state)
        assert updated["thoughts"][-1]["action"] == ActionType.RESPOND.value

    def test_think_callback(self) -> None:
        thoughts_received: List[Thought] = []

        def callback(t: Thought) -> None:
            thoughts_received.append(t)

        config = ReActConfig(thinking_callback=callback)
        orc = ReActOrc(config=config)
        state = orc._create_initial_state("Test")
        orc._think_node(state)
        assert len(thoughts_received) == 1

    @pytest.mark.anyio
    async def test_act_node_respond(self) -> None:
        orc = ReActOrc()
        state = orc._create_initial_state("Test")
        state["thoughts"].append(
            {
                "reasoning": "Done",
                "action": ActionType.RESPOND.value,
                "response_content": "Final answer",
                "tool_name": None,
                "tool_params": {},
            }
        )
        updated = await orc._act_node(state)
        assert updated["final_response"] == "Final answer"
        assert updated["should_continue"] is False

    @pytest.mark.anyio
    async def test_act_node_tool_call(self) -> None:
        orc = ReActOrc()
        orc.register_tool(CalculatorTool())
        state = orc._create_initial_state("Calculate")
        state["thoughts"].append(
            {
                "reasoning": "Need to calculate",
                "action": ActionType.TOOL_CALL.value,
                "tool_name": "calculator",
                "tool_params": {"operation": "add", "a": 5, "b": 3},
                "response_content": None,
            }
        )
        updated = await orc._act_node(state)
        assert len(updated["tool_calls"]) == 1
        assert updated["tool_calls"][0]["success"] is True
        assert updated["tool_calls"][0]["data"] == {"result": 8}

    @pytest.mark.anyio
    async def test_act_node_tool_call_no_name(self) -> None:
        orc = ReActOrc()
        state = orc._create_initial_state("Test")
        state["thoughts"].append(
            {
                "reasoning": "Call tool",
                "action": ActionType.TOOL_CALL.value,
                "tool_name": None,
                "tool_params": {},
                "response_content": None,
            }
        )
        updated = await orc._act_node(state)
        assert updated["observations"][-1]["success"] is False
        assert "No tool name" in updated["observations"][-1]["error"]

    @pytest.mark.anyio
    async def test_act_node_wait(self) -> None:
        orc = ReActOrc()
        state = orc._create_initial_state("Test")
        state["thoughts"].append(
            {
                "reasoning": "Need to wait",
                "action": ActionType.WAIT.value,
                "tool_name": None,
                "tool_params": {},
                "response_content": None,
            }
        )
        updated = await orc._act_node(state)
        assert updated["should_continue"] is False

    def test_should_continue_true(self) -> None:
        orc = ReActOrc()
        state = orc._create_initial_state("Test")
        assert orc._should_continue(state) == "think"

    def test_should_continue_false_response(self) -> None:
        orc = ReActOrc()
        state = orc._create_initial_state("Test")
        state["final_response"] = "Done"
        assert orc._should_continue(state) == "end"

    def test_should_continue_false_flag(self) -> None:
        orc = ReActOrc()
        state = orc._create_initial_state("Test")
        state["should_continue"] = False
        assert orc._should_continue(state) == "end"

    def test_should_continue_max_iterations(self) -> None:
        config = ReActConfig(max_iterations=5)
        orc = ReActOrc(config=config)
        state = orc._create_initial_state("Test")
        state["iteration"] = 5
        assert orc._should_continue(state) == "end"

    def test_build_graph(self) -> None:
        orc = ReActOrc()
        graph = orc._build_graph()
        assert graph is not None

    @pytest.mark.anyio
    async def test_execute_basic(self) -> None:
        orc = ReActOrc(config=ReActConfig(max_iterations=3))
        result = await orc.execute("What is 2+2?")
        assert "objective" in result
        assert result["objective"] == "What is 2+2?"
        assert "final_response" in result
        assert "iterations" in result

    @pytest.mark.anyio
    async def test_execute_with_custom_think(self) -> None:
        def custom_think(state: AgentState) -> Thought:
            return Thought(
                reasoning="Custom thinking",
                next_action=ActionType.RESPOND,
                response_content=f"Custom response for: {state['objective']}",
            )

        orc = ReActOrc()
        orc.set_think_fn(custom_think)
        result = await orc.execute("Test query")
        assert "Custom response" in result["final_response"]

    @pytest.mark.anyio
    async def test_execute_with_tool_call(self) -> None:
        tool_calls_made: List[Dict[str, Any]] = []

        def custom_think(state: AgentState) -> Thought:
            if not state["observations"]:
                return Thought(
                    reasoning="Need to calculate",
                    next_action=ActionType.TOOL_CALL,
                    tool_name="calculator",
                    tool_params={"operation": "multiply", "a": 6, "b": 7},
                )
            return Thought(
                reasoning="Got result",
                next_action=ActionType.RESPOND,
                response_content=f"Result: {state['observations'][-1].get('data')}",
            )

        def tool_callback(
            name: str, params: Dict[str, Any], result: ToolResult
        ) -> None:
            tool_calls_made.append({"name": name, "params": params, "result": result})

        config = ReActConfig(tool_call_callback=tool_callback)
        orc = ReActOrc(config=config)
        orc.register_tool(CalculatorTool())
        orc.set_think_fn(custom_think)

        result = await orc.execute("Calculate 6*7")
        assert len(tool_calls_made) == 1
        assert tool_calls_made[0]["name"] == "calculator"
        assert len(result["tool_calls"]) == 1

    def test_repr(self) -> None:
        config = ReActConfig(max_iterations=5)
        orc = ReActOrc(config=config)
        orc.register_tool(CalculatorTool())
        assert "tools=1" in repr(orc)
        assert "max_iter=5" in repr(orc)
