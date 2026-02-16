"""Tests for ReActHandler."""

from typing import Any, Dict

import pytest

from super.core.handler.react_handler import (
    ActionType,
    Observation,
    ReActContext,
    ReActHandler,
    Thought,
)
from super.core.tools import BaseTool, ToolCategory, ToolResult


class AddTool(BaseTool):
    """Tool that adds two numbers."""

    name = "add"
    description = "Add two numbers"
    category = ToolCategory.UTILITY

    async def execute(self, a: int = 0, b: int = 0) -> ToolResult:
        return ToolResult(success=True, data={"result": a + b})

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "integer"},
                    "b": {"type": "integer"},
                },
            },
        }


class TestThought:
    """Tests for Thought dataclass."""

    def test_thought_respond(self) -> None:
        thought = Thought(
            reasoning="I know the answer",
            next_action=ActionType.RESPOND,
            response_content="The answer is 42",
        )
        assert thought.next_action == ActionType.RESPOND
        assert thought.response_content == "The answer is 42"

    def test_thought_tool_call(self) -> None:
        thought = Thought(
            reasoning="Need to search",
            next_action=ActionType.TOOL_CALL,
            tool_name="search",
            tool_params={"query": "test"},
        )
        assert thought.next_action == ActionType.TOOL_CALL
        assert thought.tool_name == "search"
        assert thought.tool_params == {"query": "test"}


class TestObservation:
    """Tests for Observation dataclass."""

    def test_successful_observation(self) -> None:
        obs = Observation(
            action_type=ActionType.TOOL_CALL,
            success=True,
            data={"result": 10},
        )
        assert obs.success is True
        assert obs.data == {"result": 10}

    def test_failed_observation(self) -> None:
        obs = Observation(
            action_type=ActionType.TOOL_CALL,
            success=False,
            error="Tool not found",
        )
        assert obs.success is False
        assert obs.error == "Tool not found"


class TestReActContext:
    """Tests for ReActContext."""

    def test_context_init(self) -> None:
        ctx = ReActContext(objective="Test task")
        assert ctx.objective == "Test task"
        assert ctx.iteration == 0
        assert ctx.should_continue is True

    def test_add_thought(self) -> None:
        ctx = ReActContext(objective="Test")
        thought = Thought(reasoning="test", next_action=ActionType.RESPOND)
        ctx.add_thought(thought)
        assert len(ctx.thoughts) == 1

    def test_add_observation(self) -> None:
        ctx = ReActContext(objective="Test")
        obs = Observation(action_type=ActionType.RESPOND, success=True)
        ctx.add_observation(obs)
        assert len(ctx.observations) == 1

    def test_to_dict(self) -> None:
        ctx = ReActContext(objective="Test task", iteration=3)
        d = ctx.to_dict()
        assert d["objective"] == "Test task"
        assert d["iteration"] == 3


class TestReActHandler:
    """Tests for ReActHandler."""

    def test_handler_init(self) -> None:
        handler = ReActHandler()
        assert handler.name == "react_handler"
        assert handler._max_iterations == 10

    def test_handler_custom_iterations(self) -> None:
        handler = ReActHandler(max_iterations=5)
        assert handler._max_iterations == 5

    @pytest.mark.anyio
    async def test_think_no_tools(self) -> None:
        handler = ReActHandler()
        ctx = ReActContext(objective="Answer my question")
        thought = await handler.think(ctx)
        assert thought.next_action == ActionType.RESPOND

    @pytest.mark.anyio
    async def test_think_max_iterations(self) -> None:
        handler = ReActHandler(max_iterations=5)
        ctx = ReActContext(objective="Test", max_iterations=5, iteration=5)
        thought = await handler.think(ctx)
        assert thought.next_action == ActionType.RESPOND
        assert "Max iterations" in thought.reasoning

    @pytest.mark.anyio
    async def test_act_respond(self) -> None:
        handler = ReActHandler()
        thought = Thought(
            reasoning="Done",
            next_action=ActionType.RESPOND,
            response_content="Final answer",
        )
        obs = await handler.act(thought)
        assert obs.action_type == ActionType.RESPOND
        assert obs.success is True
        assert obs.data == "Final answer"

    @pytest.mark.anyio
    async def test_act_tool_call(self) -> None:
        handler = ReActHandler()
        handler.register_tool(AddTool())
        thought = Thought(
            reasoning="Need to add",
            next_action=ActionType.TOOL_CALL,
            tool_name="add",
            tool_params={"a": 5, "b": 3},
        )
        obs = await handler.act(thought)
        assert obs.action_type == ActionType.TOOL_CALL
        assert obs.success is True
        assert obs.data == {"result": 8}

    @pytest.mark.anyio
    async def test_act_tool_call_no_name(self) -> None:
        handler = ReActHandler()
        thought = Thought(
            reasoning="Call tool",
            next_action=ActionType.TOOL_CALL,
            tool_name=None,
        )
        obs = await handler.act(thought)
        assert obs.success is False
        assert "No tool name" in obs.error

    def test_observe_respond_stops_loop(self) -> None:
        handler = ReActHandler()
        ctx = ReActContext(objective="Test")
        obs = Observation(
            action_type=ActionType.RESPOND,
            success=True,
            data="Final answer",
        )
        updated = handler.observe(obs, ctx)
        assert updated.should_continue is False
        assert updated.final_response == "Final answer"

    def test_observe_increments_iteration(self) -> None:
        handler = ReActHandler()
        ctx = ReActContext(objective="Test", iteration=0)
        obs = Observation(action_type=ActionType.TOOL_CALL, success=True)
        updated = handler.observe(obs, ctx)
        assert updated.iteration == 1

    def test_should_continue(self) -> None:
        handler = ReActHandler(max_iterations=5)
        ctx = ReActContext(objective="Test", max_iterations=5)
        assert handler.should_continue(ctx) is True
        ctx.iteration = 5
        assert handler.should_continue(ctx) is False
        ctx.iteration = 2
        ctx.should_continue = False
        assert handler.should_continue(ctx) is False

    @pytest.mark.anyio
    async def test_execute_basic(self) -> None:
        handler = ReActHandler(max_iterations=3)
        result = await handler.execute("What is 2+2?")
        assert "objective" in result
        assert "final_response" in result
        assert result["iterations"] > 0

    def test_repr(self) -> None:
        handler = ReActHandler(max_iterations=5)
        handler.register_tool(AddTool())
        assert "tools=1" in repr(handler)
        assert "max_iter=5" in repr(handler)

    def test_dump(self) -> None:
        handler = ReActHandler(max_iterations=7)
        dump = handler.dump
        assert dump["name"] == "react_handler"
        assert dump["max_iterations"] == 7
