"""Tests for tool adapters."""

import json
from typing import Any, Dict

import pytest

from super.core.tools import ToolRegistry
from super.core.tools.adapters import (
    CentralToolPlugin,
    create_superkik_compatible_registry,
    tool_to_function_tool,
    tool_to_langgraph_tool,
)
from super.core.tools.base import BaseTool, ToolCategory, ToolResult


class EchoTool(BaseTool):
    """Simple echo tool for testing adapters."""

    name = "echo"
    description = "Echo the input message"
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
    """Tool that fails for testing error handling."""

    name = "failing"
    description = "Always fails"
    category = ToolCategory.UTILITY

    async def execute(self, **kwargs: Any) -> ToolResult:
        return ToolResult(success=False, error="Intentional failure")

    def get_schema(self) -> Dict[str, Any]:
        return {"name": self.name, "parameters": {"type": "object", "properties": {}}}


class TestToolToFunctionTool:
    """Tests for tool_to_function_tool adapter."""

    @pytest.mark.anyio
    async def test_successful_execution(self) -> None:
        tool = EchoTool()
        func = tool_to_function_tool(tool)

        result_str = await func(message="hello")
        result = json.loads(result_str)

        assert result["status"] == "success"
        assert result["data"]["echo"] == "hello"

    @pytest.mark.anyio
    async def test_failed_execution(self) -> None:
        tool = FailingTool()
        func = tool_to_function_tool(tool)

        result_str = await func()
        result = json.loads(result_str)

        assert result["status"] == "failed"
        assert "Intentional failure" in result["error"]

    def test_function_name_preserved(self) -> None:
        tool = EchoTool()
        func = tool_to_function_tool(tool)

        assert func.__name__ == "echo"

    def test_function_doc_preserved(self) -> None:
        tool = EchoTool()
        func = tool_to_function_tool(tool)

        assert func.__doc__ == "Echo the input message"


class TestToolToLangGraphTool:
    """Tests for tool_to_langgraph_tool adapter."""

    def test_conversion(self) -> None:
        tool = EchoTool()
        lg_tool = tool_to_langgraph_tool(tool)

        assert lg_tool["name"] == "echo"
        assert lg_tool["description"] == "Echo the input message"
        assert "func" in lg_tool
        assert "schema" in lg_tool

    @pytest.mark.anyio
    async def test_langgraph_execution(self) -> None:
        tool = EchoTool()
        lg_tool = tool_to_langgraph_tool(tool)

        result = await lg_tool["func"](message="test")
        data = json.loads(result)

        assert data["echo"] == "test"


class TestCentralToolPlugin:
    """Tests for CentralToolPlugin adapter."""

    def test_plugin_creation(self) -> None:
        plugin = CentralToolPlugin(
            name="test_plugin",
            tools=[EchoTool(), FailingTool()],
        )

        assert plugin.name == "test_plugin"
        assert plugin.enabled is True
        assert len(plugin.get_tool_names()) == 2

    @pytest.mark.anyio
    async def test_plugin_initialization(self) -> None:
        plugin = CentralToolPlugin(
            name="test_plugin",
            tools=[EchoTool()],
        )

        await plugin.initialize(handler=None)

        functions = plugin.get_tool_functions()
        assert len(functions) == 1

    @pytest.mark.anyio
    async def test_plugin_disabled(self) -> None:
        plugin = CentralToolPlugin(
            name="test_plugin",
            tools=[EchoTool()],
            enabled=False,
        )

        await plugin.initialize(handler=None)

        functions = plugin.get_tool_functions()
        assert len(functions) == 0

    @pytest.mark.anyio
    async def test_plugin_enable_disable(self) -> None:
        plugin = CentralToolPlugin(
            name="test_plugin",
            tools=[EchoTool()],
        )

        await plugin.initialize(handler=None)

        assert len(plugin.get_tool_functions()) == 1

        plugin.set_enabled(False)
        assert len(plugin.get_tool_functions()) == 0

        plugin.set_enabled(True)
        assert len(plugin.get_tool_functions()) == 1

    def test_plugin_metrics(self) -> None:
        plugin = CentralToolPlugin(
            name="test_plugin",
            tools=[EchoTool(), FailingTool()],
        )

        metrics = plugin.get_metrics()

        assert metrics["name"] == "test_plugin"
        assert metrics["enabled"] is True
        assert metrics["tool_count"] == 2
        assert "echo" in metrics["tools"]
        assert "failing" in metrics["tools"]


class TestCreateSuperkikCompatibleRegistry:
    """Tests for create_superkik_compatible_registry helper."""

    def test_creation(self) -> None:
        registry = ToolRegistry()
        registry.register(EchoTool())
        registry.register(FailingTool())

        plugin = create_superkik_compatible_registry(
            registry, plugin_name="my_tools"
        )

        assert plugin.name == "my_tools"
        assert len(plugin.get_tool_names()) == 2

    @pytest.mark.anyio
    async def test_full_integration(self) -> None:
        registry = ToolRegistry()
        registry.register(EchoTool())

        plugin = create_superkik_compatible_registry(registry)
        await plugin.initialize(handler=None)

        functions = plugin.get_tool_functions()
        assert len(functions) == 1

        result_str = await functions[0](message="integration test")
        result = json.loads(result_str)

        assert result["status"] == "success"
        assert result["data"]["echo"] == "integration test"
