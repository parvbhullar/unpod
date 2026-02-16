"""Tests for BaseTool and ToolRegistry."""

from typing import Any, Dict

import pytest

from super.core.tools.base import BaseTool, ToolCategory, ToolRegistry, ToolResult


class EchoTool(BaseTool):
    """Simple echo tool for testing."""

    name = "echo"
    description = "Echoes the input message"
    category = ToolCategory.UTILITY

    async def execute(self, message: str = "") -> ToolResult:
        return ToolResult(success=True, data={"echo": message})

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Message to echo"},
                },
                "required": ["message"],
            },
        }


class SearchTool(BaseTool):
    """Search tool for testing category filtering."""

    name = "search"
    description = "Searches for data"
    category = ToolCategory.SEARCH

    async def execute(self, query: str = "") -> ToolResult:
        return ToolResult(success=True, data={"results": [query]})

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                },
                "required": ["query"],
            },
        }


class FailingTool(BaseTool):
    """Tool that always raises an exception."""

    name = "failing_tool"
    description = "Always fails"
    category = ToolCategory.UTILITY

    async def execute(self, **kwargs: Any) -> ToolResult:
        raise ValueError("Intentional failure")

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {"type": "object", "properties": {}},
        }


class TestToolResult:
    """Tests for ToolResult dataclass."""

    def test_success_result(self) -> None:
        result = ToolResult(success=True, data={"key": "value"})
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.error is None
        assert result.metadata == {}

    def test_error_result(self) -> None:
        result = ToolResult(success=False, error="Something went wrong")
        assert result.success is False
        assert result.data is None
        assert result.error == "Something went wrong"

    def test_result_with_metadata(self) -> None:
        result = ToolResult(
            success=True,
            data="test",
            metadata={"duration_ms": 100, "source": "api"},
        )
        assert result.metadata["duration_ms"] == 100
        assert result.metadata["source"] == "api"


class TestBaseTool:
    """Tests for BaseTool base class."""

    def test_tool_name(self) -> None:
        tool = EchoTool()
        assert tool.name == "echo"

    def test_tool_description(self) -> None:
        tool = EchoTool()
        assert tool.description == "Echoes the input message"

    def test_tool_category(self) -> None:
        tool = EchoTool()
        assert tool.category == ToolCategory.UTILITY

    def test_tool_repr(self) -> None:
        tool = EchoTool()
        assert repr(tool) == "EchoTool(name=echo)"

    @pytest.mark.anyio
    async def test_tool_execute(self) -> None:
        tool = EchoTool()
        result = await tool.execute(message="hello")
        assert result.success is True
        assert result.data == {"echo": "hello"}

    def test_tool_schema(self) -> None:
        tool = EchoTool()
        schema = tool.get_schema()
        assert schema["name"] == "echo"
        assert "parameters" in schema
        assert schema["parameters"]["properties"]["message"]["type"] == "string"


class TestToolRegistry:
    """Tests for ToolRegistry."""

    def test_register_tool(self) -> None:
        registry = ToolRegistry()
        tool = EchoTool()
        registry.register(tool)
        assert "echo" in registry
        assert len(registry) == 1

    def test_get_tool(self) -> None:
        registry = ToolRegistry()
        tool = EchoTool()
        registry.register(tool)
        retrieved = registry.get("echo")
        assert retrieved is tool

    def test_get_nonexistent_tool(self) -> None:
        registry = ToolRegistry()
        assert registry.get("nonexistent") is None

    def test_list_tools(self) -> None:
        registry = ToolRegistry()
        registry.register(EchoTool())
        registry.register(SearchTool())
        tools = registry.list_tools()
        assert sorted(tools) == ["echo", "search"]

    def test_get_all_schemas(self) -> None:
        registry = ToolRegistry()
        registry.register(EchoTool())
        registry.register(SearchTool())
        schemas = registry.get_all_schemas()
        assert len(schemas) == 2
        names = {s["name"] for s in schemas}
        assert names == {"echo", "search"}

    def test_get_tools_by_category(self) -> None:
        registry = ToolRegistry()
        registry.register(EchoTool())
        registry.register(SearchTool())
        search_tools = registry.get_tools_by_category(ToolCategory.SEARCH)
        assert len(search_tools) == 1
        assert search_tools[0].name == "search"

    @pytest.mark.anyio
    async def test_execute_tool(self) -> None:
        registry = ToolRegistry()
        registry.register(EchoTool())
        result = await registry.execute("echo", message="world")
        assert result.success is True
        assert result.data == {"echo": "world"}

    @pytest.mark.anyio
    async def test_execute_nonexistent_tool(self) -> None:
        registry = ToolRegistry()
        result = await registry.execute("nonexistent")
        assert result.success is False
        assert "Tool not found" in result.error

    @pytest.mark.anyio
    async def test_execute_failing_tool(self) -> None:
        registry = ToolRegistry()
        registry.register(FailingTool())
        result = await registry.execute("failing_tool")
        assert result.success is False
        assert "Tool execution failed" in result.error
        assert result.metadata["exception_type"] == "ValueError"

    def test_contains(self) -> None:
        registry = ToolRegistry()
        registry.register(EchoTool())
        assert "echo" in registry
        assert "nonexistent" not in registry


class TestToolCategory:
    """Tests for ToolCategory enum."""

    def test_category_values(self) -> None:
        assert ToolCategory.SEARCH.value == "search"
        assert ToolCategory.COMMUNICATION.value == "communication"
        assert ToolCategory.DATA_PROCESSING.value == "data_processing"
        assert ToolCategory.BOOKING.value == "booking"
        assert ToolCategory.KNOWLEDGE.value == "knowledge"
        assert ToolCategory.UTILITY.value == "utility"
