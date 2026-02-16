"""
ToolCallHandler - Handler with tool execution capability.

Extends BaseHandler to provide tool calling functionality through
a ToolRegistry. This is the foundation for agentic handlers.
"""

from typing import Any, Dict, List, Optional

from super.core.handler.base import BaseHandler
from super.core.logging import logging as app_logging
from super.core.tools import BaseTool, ToolRegistry, ToolResult

logger = app_logging.get_logger("handler.tool")


class ToolCallHandler(BaseHandler):
    """
    Handler that can execute tools through a ToolRegistry.

    Provides the foundation for tool-using agents. Tools are stateless
    and managed by the registry.
    """

    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        **kwargs: Any,
    ) -> None:
        self._tool_registry = tool_registry or ToolRegistry()
        self._tool_call_history: List[Dict[str, Any]] = []

    @property
    def name(self) -> str:
        return "tool_call_handler"

    @property
    def dump(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "tools": self._tool_registry.list_tools(),
            "tool_call_count": len(self._tool_call_history),
        }

    def __repr__(self) -> str:
        tool_count = len(self._tool_registry)
        return f"ToolCallHandler(tools={tool_count})"

    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool with the handler's registry."""
        self._tool_registry.register(tool)

    def register_tools(self, tools: List[BaseTool]) -> None:
        """Register multiple tools."""
        for tool in tools:
            self._tool_registry.register(tool)

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get OpenAI-compatible schemas for all registered tools."""
        return self._tool_registry.get_all_schemas()

    async def call_tool(self, name: str, **kwargs: Any) -> ToolResult:
        """
        Execute a tool by name.

        Args:
            name: Tool name
            **kwargs: Tool parameters

        Returns:
            ToolResult with execution outcome
        """
        result = await self._tool_registry.execute(name, **kwargs)

        self._tool_call_history.append(
            {
                "tool": name,
                "params": kwargs,
                "success": result.success,
                "error": result.error,
            }
        )

        return result

    async def execute(self, objective: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Execute the handler with an objective.

        This base implementation just returns the objective.
        Subclasses should override with actual logic.

        Args:
            objective: The task/goal to accomplish

        Returns:
            Dict with execution result
        """
        return {
            "objective": objective,
            "tools_available": self._tool_registry.list_tools(),
            "message": "ToolCallHandler does not implement execute logic directly",
        }

    def get_tool_call_history(self) -> List[Dict[str, Any]]:
        """Return history of tool calls made by this handler."""
        return self._tool_call_history.copy()

    def clear_tool_call_history(self) -> None:
        """Clear the tool call history."""
        self._tool_call_history.clear()
