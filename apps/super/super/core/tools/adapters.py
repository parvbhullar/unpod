"""
Tool Adapters - Bridge between central tools and framework-specific implementations.

Provides adapters to use central BaseTool implementations with:
- SuperKik's ToolPlugin system (pydantic-ai @function_tool)
- LangGraph tool interfaces
- Other agent frameworks
"""

import json
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from super.core.logging import logging as app_logging
from super.core.tools.base import BaseTool, ToolRegistry, ToolResult

if TYPE_CHECKING:
    from super.core.voice.superkik.tools.base import ToolPlugin

logger = app_logging.get_logger("tools.adapters")


def tool_to_function_tool(tool: BaseTool) -> Callable:
    """
    Convert a BaseTool to a pydantic-ai @function_tool decorated function.

    This allows central tools to be used with SuperKik's existing
    ToolPluginRegistry system.

    Args:
        tool: BaseTool instance to wrap

    Returns:
        Async function decorated with @function_tool
    """
    try:
        from livekit.agents.llm import function_tool
    except ImportError:
        logger.warning("livekit.agents not available, returning passthrough")

        async def passthrough(**kwargs: Any) -> str:
            result = await tool.execute(**kwargs)
            return json.dumps(
                {"success": result.success, "data": result.data, "error": result.error}
            )

        passthrough.__name__ = tool.name
        passthrough.__doc__ = tool.description
        return passthrough

    @function_tool
    async def wrapped_tool(**kwargs: Any) -> str:
        """Wrapped tool execution."""
        try:
            result = await tool.execute(**kwargs)

            if result.success:
                return json.dumps(
                    {
                        "status": "success",
                        "data": result.data,
                        "message": f"{tool.name} completed successfully",
                    }
                )
            else:
                return json.dumps(
                    {
                        "status": "failed",
                        "error": result.error,
                        "message": f"{tool.name} failed: {result.error}",
                    }
                )

        except Exception as e:
            logger.error(f"{tool.name} execution error: {e}")
            return json.dumps(
                {
                    "status": "error",
                    "message": f"Error executing {tool.name}: {e}",
                }
            )

    wrapped_tool.__name__ = tool.name
    wrapped_tool.__doc__ = tool.description

    return wrapped_tool


def registry_to_function_tools(registry: ToolRegistry) -> List[Callable]:
    """
    Convert all tools in a registry to function_tool decorated functions.

    Args:
        registry: ToolRegistry with tools to convert

    Returns:
        List of @function_tool decorated functions
    """
    return [tool_to_function_tool(registry.get(name)) for name in registry.list_tools()]


def tool_to_langgraph_tool(tool: BaseTool) -> Dict[str, Any]:
    """
    Convert a BaseTool to LangGraph tool format.

    Args:
        tool: BaseTool instance to convert

    Returns:
        Dict with name, description, and func for LangGraph
    """

    async def execute_wrapper(**kwargs: Any) -> str:
        result = await tool.execute(**kwargs)
        if result.success:
            return json.dumps(result.data) if result.data else "Success"
        return f"Error: {result.error}"

    return {
        "name": tool.name,
        "description": tool.description,
        "func": execute_wrapper,
        "schema": tool.get_schema(),
    }


class CentralToolPlugin:
    """
    Adapter that wraps central BaseTool instances as a SuperKik-compatible plugin.

    This allows the new central tools to be used within SuperKik's
    existing ToolPluginRegistry system.

    Usage:
        from super.core.tools import PlacesTool, ExaWebSearchTool
        from super.core.tools.adapters import CentralToolPlugin

        # Create adapter with central tools
        plugin = CentralToolPlugin(
            name="central",
            tools=[PlacesTool(), ExaWebSearchTool()],
        )

        # Register with SuperKik's registry
        registry.register_plugin(plugin)
    """

    def __init__(
        self,
        name: str,
        tools: List[BaseTool],
        enabled: bool = True,
    ) -> None:
        self.name = name
        self._tools = tools
        self.enabled = enabled
        self._handler: Optional[Any] = None
        self._function_tools: List[Callable] = []

    async def initialize(self, handler: Any) -> None:
        """Initialize the plugin with a handler reference."""
        self._handler = handler
        self._function_tools = [tool_to_function_tool(t) for t in self._tools]
        logger.info(f"CentralToolPlugin '{self.name}' initialized with {len(self._tools)} tools")

    def get_tool_functions(self) -> List[Callable]:
        """Get all tool functions for this plugin."""
        if not self.enabled:
            return []
        return self._function_tools

    def get_tool_names(self) -> List[str]:
        """Get names of all tools in this plugin."""
        return [t.name for t in self._tools]

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the plugin."""
        self.enabled = enabled

    def get_metrics(self) -> Optional[Dict[str, Any]]:
        """Return plugin metrics."""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "tool_count": len(self._tools),
            "tools": self.get_tool_names(),
        }

    async def cleanup(self) -> None:
        """Cleanup plugin resources."""
        pass


def create_superkik_compatible_registry(
    central_registry: ToolRegistry,
    plugin_name: str = "central_tools",
) -> CentralToolPlugin:
    """
    Create a SuperKik-compatible plugin from a central ToolRegistry.

    Args:
        central_registry: ToolRegistry with tools
        plugin_name: Name for the plugin

    Returns:
        CentralToolPlugin that can be used with SuperKik
    """
    tools = [central_registry.get(name) for name in central_registry.list_tools()]
    return CentralToolPlugin(name=plugin_name, tools=tools)
