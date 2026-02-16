"""
Objection Manager for Section-Based Flows

Manages objection handlers that can be triggered at any point in the conversation.
Injects objection handlers into all nodes as global functions.
"""

from typing import List
from pipecat_flows import NodeConfig, FlowsFunctionSchema
from .section_parser import ParsedSection, ParsedFlowConfig
from .handler_factory import HandlerFactory


class ObjectionManager:
    """
    Manages objection handlers that can interrupt flow at any point.

    Objection handlers are special because they:
    - Can be triggered from ANY node in the flow
    - Return to the previous section after handling
    - Are injected into all nodes as additional functions
    """

    def __init__(self, flow_config: ParsedFlowConfig, handler_factory: HandlerFactory):
        self.config = flow_config
        self.handler_factory = handler_factory
        self.objection_functions = []  # Cached function schemas

    def get_objection_functions(self) -> List[FlowsFunctionSchema]:
        """
        Get function schemas for all objection handlers.

        Returns:
            List of FlowsFunctionSchema objects for objections
        """
        if self.objection_functions:
            return self.objection_functions

        # Create function schema for each objection section
        for objection_section in self.config.objections:
            function_schema = self._create_objection_function(objection_section)
            self.objection_functions.append(function_schema)

        return self.objection_functions

    def _create_objection_function(self, section: ParsedSection) -> FlowsFunctionSchema:
        """Create FlowsFunctionSchema for an objection handler."""

        # Get handler from factory
        handler = self.handler_factory.create_handler_for_section(section)

        # Build properties
        properties = {
            "objection_type": {
                "type": "string",
                "description": f"Type of objection: {section.section_name}",
            },
            "details": {
                "type": "string",
                "description": "Additional details about the objection"
            }
        }

        if section.trigger_keywords:
            properties["objection_type"]["enum"] = section.trigger_keywords

        # Add any section-specific required fields
        for field in section.required:
            if field not in properties:
                properties[field] = {
                    "type": "string",
                    "description": f"User's response for {field}"
                }

        # Create function schema
        function_name = f"handle_objection_{section.id}"

        return FlowsFunctionSchema(
            name=function_name,
            handler=handler,
            description=f"Handle customer objection: {section.section_name}",
            properties=properties,
            required=["objection_type"]  # Only objection_type is required
        )

    def inject_objection_handlers_into_nodes(self, nodes: List[NodeConfig]) -> List[NodeConfig]:
        """
        Add objection handlers to all nodes.

        Args:
            nodes: List of NodeConfig objects

        Returns:
            Same list of nodes with objection handlers added
        """
        # Get objection functions
        objection_functions = self.get_objection_functions()

        if not objection_functions:
            # No objections to inject
            return nodes

        # Add objection functions to each node (supports NodeConfig or dict payloads)
        for idx, node in enumerate(nodes):
            if isinstance(node, dict):
                existing_functions = list(node.get("functions", []))
                existing_names = set()
                for func in existing_functions:
                    if hasattr(func, "name"):
                        name = getattr(func, "name", None)
                        if name:
                            existing_names.add(name)
                    elif isinstance(func, dict):
                        name = func.get("name")
                        if name:
                            existing_names.add(name)
                for obj_func in objection_functions:
                    if obj_func.name not in existing_names:
                        existing_functions.append(obj_func)
                        existing_names.add(obj_func.name)
                node["functions"] = existing_functions
                nodes[idx] = node
            else:
                existing_functions = list(getattr(node, "functions", [])) if getattr(node, "functions", None) else []
                existing_names = {getattr(f, "name", None) for f in existing_functions if getattr(f, "name", None)}
                for obj_func in objection_functions:
                    if obj_func.name not in existing_names:
                        existing_functions.append(obj_func)
                        existing_names.add(obj_func.name)
                node.functions = existing_functions

        return nodes

    def get_objection_sections(self) -> List[ParsedSection]:
        """Get all objection sections."""
        return list(self.config.objections)

    def has_objections(self) -> bool:
        """Check if any objection handlers exist."""
        return len(self.config.objections) > 0
