"""
Central Tool System for ReAct Orchestrator.

Provides a generic tool interface for agentic workflows. Tools are stateless
and managed by ToolRegistry. This design allows tools to work with multiple
agent frameworks (LangGraph, pydantic-ai, etc.).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ToolCategory(Enum):
    """Categories for organizing tools."""

    SEARCH = "search"
    COMMUNICATION = "communication"
    DATA_PROCESSING = "data_processing"
    BOOKING = "booking"
    KNOWLEDGE = "knowledge"
    UTILITY = "utility"


@dataclass
class ToolResult:
    """Result from tool execution."""

    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseTool(ABC):
    """
    Abstract base class for tools.

    Tools are stateless execution units. Each tool provides:
    - name: Unique identifier
    - description: Human-readable description
    - category: For grouping related tools
    - execute: Async execution method
    - get_schema: JSON schema for parameters
    """

    name: str = "base_tool"
    description: str = "Base tool"
    category: ToolCategory = ToolCategory.UTILITY

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """
        Execute the tool with given parameters.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            ToolResult with success status and data/error
        """
        ...

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        Return JSON schema for tool parameters.

        Returns:
            OpenAI function calling compatible schema
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"


class ToolRegistry:
    """
    Registry for managing tool instances.

    Handles registration, lookup, and execution of tools.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """
        Register a tool instance.

        Args:
            tool: Tool instance to register
        """
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """Return list of registered tool names."""
        return list(self._tools.keys())

    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """Return schemas for all registered tools."""
        return [tool.get_schema() for tool in self._tools.values()]

    def get_tools_by_category(self, category: ToolCategory) -> List[BaseTool]:
        """
        Get all tools in a category.

        Args:
            category: Tool category to filter by

        Returns:
            List of tools in the category
        """
        return [t for t in self._tools.values() if t.category == category]

    async def execute(self, name: str, **kwargs: Any) -> ToolResult:
        """
        Execute a tool by name.

        Args:
            name: Tool name
            **kwargs: Tool parameters

        Returns:
            ToolResult from tool execution
        """
        tool = self.get(name)
        if not tool:
            return ToolResult(success=False, error=f"Tool not found: {name}")
        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Tool execution failed: {e}",
                metadata={"exception_type": type(e).__name__},
            )

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools
