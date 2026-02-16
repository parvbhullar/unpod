"""
ToolsManager - Centralized tools/functions definition for voice services.

This module provides a unified interface for defining and creating tools (functions)
that can be used by both the prompt manager and pipecat services (including OpenAI Realtime API).
"""

from typing import List, Dict, Any, Optional
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema


class ToolsManager:
    """Manages tool definitions for voice services based on configuration."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize ToolsManager with configuration.

        Args:
            config: Configuration dictionary containing tool settings
        """
        self.config = config

    def build_function_schemas(self) -> List[FunctionSchema]:
        """
        Build list of FunctionSchema objects based on configuration.

        Returns:
            List of FunctionSchema objects for pipecat services
        """
        tools = []

        # Add get_knowledge_base_info tool if knowledge bases are configured
        knowledge_bases = self.config.get("knowledge_base", [])
        if knowledge_bases and len(knowledge_bases) > 0:
            tools.append(
                FunctionSchema(
                    name="get_knowledge_base_info",
                    description="Fetch relevant docs from knowledge bases to answer user query",
                    properties={
                        "query": {"type": "string", "description": "The text to search for"},
                        "kn_name": {"type": "string", "description": "Which KB to restrict to"},
                    },
                    required=["query", "kn_name"]
                )
            )

        # Add handover_call tool if handover_number is configured
        if self.config.get("handover_number"):
            tools.append(
                FunctionSchema(
                    name="handover_call",
                    description="Handover the call to human manager, supervisor or owner",
                    properties={},
                    required=[],
                )
            )

        # Add switch_language tool if dual_language is enabled
        if self.config.get("dual_language", False):
            tools.append(
                FunctionSchema(
                    name="switch_language",
                    description="Switch TTS output to the requested or last spoken language (english or secondary).",
                    properties={
                        "language": {"type": "string", "description": "Language code to switch to (e.g., 'en', 'hi')."}
                    },
                    required=["language"],
                )
            )

        return tools

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """
        Build list of tools in OpenAI API format for Realtime API.

        Returns:
            List of tool dictionaries in OpenAI format
        """
        standard_tools = self.build_function_schemas()

        # Convert FunctionSchema to OpenAI tools format
        tools = ToolsSchema(standard_tools=standard_tools)
        return tools

    def get_tool_names(self) -> List[str]:
        """
        Get list of available tool names based on configuration.

        Returns:
            List of tool names as strings
        """
        schemas = self.build_function_schemas()
        return [schema.name for schema in schemas]
