"""Tests for ToolCallHandler."""

from typing import Any, Dict

import pytest

from super.core.handler.tool_handler import ToolCallHandler
from super.core.tools import BaseTool, ToolCategory, ToolRegistry, ToolResult


class EchoTool(BaseTool):
    """Simple echo tool for testing."""

    name = "echo"
    description = "Echoes the input"
    category = ToolCategory.UTILITY

    async def execute(self, message: str = "") -> ToolResult:
        return ToolResult(success=True, data={"echo": message})

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {"message": {"type": "string"}},
                "required": ["message"],
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


class TestToolCallHandler:
    """Tests for ToolCallHandler."""

    def test_handler_init(self) -> None:
        handler = ToolCallHandler()
        assert handler.name == "tool_call_handler"
        assert len(handler._tool_registry) == 0

    def test_handler_with_registry(self) -> None:
        registry = ToolRegistry()
        registry.register(EchoTool())
        handler = ToolCallHandler(tool_registry=registry)
        assert len(handler._tool_registry) == 1

    def test_register_tool(self) -> None:
        handler = ToolCallHandler()
        handler.register_tool(EchoTool())
        assert "echo" in handler._tool_registry

    def test_register_tools(self) -> None:
        handler = ToolCallHandler()
        handler.register_tools([EchoTool(), FailingTool()])
        assert len(handler._tool_registry) == 2

    def test_get_tool_schemas(self) -> None:
        handler = ToolCallHandler()
        handler.register_tool(EchoTool())
        schemas = handler.get_tool_schemas()
        assert len(schemas) == 1
        assert schemas[0]["name"] == "echo"

    @pytest.mark.anyio
    async def test_call_tool_success(self) -> None:
        handler = ToolCallHandler()
        handler.register_tool(EchoTool())
        result = await handler.call_tool("echo", message="hello")
        assert result.success is True
        assert result.data == {"echo": "hello"}

    @pytest.mark.anyio
    async def test_call_tool_failure(self) -> None:
        handler = ToolCallHandler()
        handler.register_tool(FailingTool())
        result = await handler.call_tool("failing")
        assert result.success is False
        assert "Intentional failure" in result.error

    @pytest.mark.anyio
    async def test_call_nonexistent_tool(self) -> None:
        handler = ToolCallHandler()
        result = await handler.call_tool("nonexistent")
        assert result.success is False
        assert "not found" in result.error

    @pytest.mark.anyio
    async def test_tool_call_history(self) -> None:
        handler = ToolCallHandler()
        handler.register_tool(EchoTool())
        await handler.call_tool("echo", message="first")
        await handler.call_tool("echo", message="second")

        history = handler.get_tool_call_history()
        assert len(history) == 2
        assert history[0]["tool"] == "echo"
        assert history[0]["params"] == {"message": "first"}
        assert history[1]["params"] == {"message": "second"}

    @pytest.mark.anyio
    async def test_clear_tool_call_history(self) -> None:
        handler = ToolCallHandler()
        handler.register_tool(EchoTool())
        await handler.call_tool("echo", message="test")
        assert len(handler.get_tool_call_history()) == 1
        handler.clear_tool_call_history()
        assert len(handler.get_tool_call_history()) == 0

    def test_repr(self) -> None:
        handler = ToolCallHandler()
        handler.register_tools([EchoTool(), FailingTool()])
        assert "tools=2" in repr(handler)

    def test_dump(self) -> None:
        handler = ToolCallHandler()
        handler.register_tool(EchoTool())
        dump = handler.dump
        assert dump["name"] == "tool_call_handler"
        assert "echo" in dump["tools"]
