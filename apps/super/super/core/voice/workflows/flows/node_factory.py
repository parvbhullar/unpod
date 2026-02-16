"""
Node Factory for Section-Based Flows

Creates NodeConfig objects from ParsedSection objects with specialized handlers.
Preserves multi-language content and exact phrasing.
"""

from typing import Dict, List, Any
from pipecat_flows import NodeConfig, FlowsFunctionSchema
from .section_parser import ParsedSection, ParsedFlowConfig
from .handler_factory import HandlerFactory


class NodeConfigWrapper(dict):
    """
    Dict subclass that provides attribute-style access to node config keys.

    This keeps compatibility with the TypedDict-based NodeConfig structure used by
    pipecat_flows while letting downstream code access fields as attributes.
    """

    __slots__ = ()

    def __getattr__(self, item: str) -> Any:
        try:
            return self[item]
        except KeyError as exc:
            raise AttributeError(item) from exc

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value

    def __delattr__(self, item: str) -> None:
        if item in self:
            del self[item]
        else:
            raise AttributeError(item)

    def copy(self) -> "NodeConfigWrapper":
        return NodeConfigWrapper(super().copy())


class NodeFactory:
    """
    Factory for creating NodeConfig objects from ParsedSection objects.

    Creates:
    - FlowsFunctionSchema with custom handler
    - Role messages (generic instructions)
    - Task messages (section-specific content - PRESERVES ORIGINAL)
    - Complete NodeConfig ready for FlowManager
    """

    def __init__(
        self,
        flow_config: ParsedFlowConfig,
        handler_factory: HandlerFactory,
        assistant_prompt: str = None
    ):
        self.config = flow_config
        self.handler_factory = handler_factory
        self.assistant_prompt = assistant_prompt  # Full assistant prompt from PromptManager
        self.node_cache = {}  # Cache created nodes

    def create_node_for_section(self, section: ParsedSection) -> NodeConfig:
        """
        Create NodeConfig for a section.

        Args:
            section: ParsedSection to create node for

        Returns:
            NodeConfig ready for FlowManager
        """
        # Check cache
        if section.id in self.node_cache:
            return self.node_cache[section.id]

        # Get handler for this section
        handler = self.handler_factory.create_handler_for_section(section)

        # Create function schema
        function_schema = self._create_function_schema(section, handler)

        # Create role messages
        role_messages = self._create_role_messages(section)

        # Create task messages (PRESERVE ORIGINAL CONTENT)
        task_messages = self._create_task_messages(section)

        # Build NodeConfig
        node_dict: NodeConfig = NodeConfig(
            name=section.id,
            respond_immediately=True,
            role_messages=role_messages,
            task_messages=task_messages,
            functions=[function_schema]
        )

        node = NodeConfigWrapper(node_dict)

        # Cache and return
        self.node_cache[section.id] = node
        return node

    def _create_function_schema(
        self,
        section: ParsedSection,
        handler
    ) -> FlowsFunctionSchema:
        """Create FlowsFunctionSchema for section."""

        # Build properties from required fields
        properties = {}
        for field in section.required:
            field_type = section.field_types.get(field, 'string')
            field_description = section.field_descriptions.get(
                field,
                f"User's response for {field}"
            )

            # Map field types to JSON schema types
            if field_type == 'boolean':
                properties[field] = {
                    "type": "boolean",
                    "description": field_description
                }
            elif field_type == 'number':
                properties[field] = {
                    "type": "number",
                    "description": field_description or f"Numeric value for {field}"
                }
            elif field_type == 'enum':
                # Try to extract enum values from content
                enum_values = self._extract_enum_values(section.content, field)
                properties[field] = {
                    "type": "string",
                    "description": field_description,
                }
                if enum_values:
                    properties[field]["enum"] = enum_values
            else:
                # Default: string
                properties[field] = {
                    "type": "string",
                    "description": field_description
                }

        # Create function schema
        function_name = f"collect_{section.id}"
        if section.type == 'objection':
            function_name = f"handle_{section.id}"
        elif section.type == 'condition':
            function_name = f"evaluate_{section.id}"

        return FlowsFunctionSchema(
            name=function_name,
            handler=handler,
            description=section.description or f"Process {section.section_name}",
            properties=properties,
            required=section.required
        )

    def _create_role_messages(self, section: ParsedSection) -> List[Dict]:
        """
        Create role messages (generic instructions).

        Incorporates full assistant_prompt from PromptManager to ensure context consistency
        across all nodes. This includes:
        - Agent identity, name, gender, timezone
        - Professional/casual/basic tone prompts
        - Current date/time
        - Call type (inbound/outbound)
        - Full system prompt with identity, rules, guidelines
        """

        # Build section-specific instruction
        if section.type == 'greeting':
            step_instruction = (
                f"**CURRENT STEP:** {section.section_name}\n\n"
                f"You must ALWAYS use the collect_{section.id} function to collect required information. "
                "Be warm and professional in your greeting."
            )
        elif section.type == 'question':
            step_instruction = (
                f"**CURRENT STEP:** {section.section_name}\n\n"
                f"You must ALWAYS use the collect_{section.id} function to collect: {', '.join(section.required)}. "
                "Ask clearly and wait for the user's response before proceeding."
            )
        elif section.type == 'pitch':
            step_instruction = (
                f"**CURRENT STEP:** {section.section_name}\n\n"
                f"You must use the collect_{section.id} function after presenting the offer. "
                "Be persuasive but not pushy. Highlight value clearly."
            )
        elif section.type == 'condition':
            step_instruction = (
                f"**CURRENT STEP:** {section.section_name}\n\n"
                f"You must use the evaluate_{section.id} function to determine the next step. "
                "Follow the user's response to branch appropriately."
            )
        elif section.type == 'objection':
            step_instruction = (
                f"**CURRENT STEP:** Handling Objection - {section.section_name}\n\n"
                f"You must use the handle_{section.id} function when addressing this objection. "
                "Be empathetic, address concerns directly, and guide back to value proposition."
            )
        else:
            # Generic
            step_instruction = (
                f"**CURRENT STEP:** {section.section_name}\n\n"
                f"You must use the {section.id} function to progress the conversation. "
                "Be professional and friendly."
            )

        # Construct final content with full context
        content = ""
        if self.assistant_prompt:
            # CRITICAL FIX: Prepend full assistant prompt for context consistency
            # This ensures agent identity, rules, guidelines are present in every node
            content += f"{self.assistant_prompt}"
            # Fallback: minimal context (backward compatibility)
        if self.config.identity:
            identity_content = self.config.identity.content.strip()
            # Only add first few lines to avoid bloat
            identity_lines = identity_content.split('\n')
            identity_summary = '\n'.join(identity_lines)
            content += f"{identity_summary}\n\n{step_instruction}"

        content += f"\n\n{'='*60}\n\n{step_instruction}"

        return [
            {
                "role": "system",
                "content": content
            }
        ]

    def _create_task_messages(self, section: ParsedSection) -> List[Dict]:
        """
        Create task messages (PRESERVES ORIGINAL CONTENT).

        This is critical - must preserve:
        - Multi-language content (English + Hindi)
        - Exact phrasing and amounts
        - Template variables ({{name}})
        - Wait states
        - Formatting
        """

        # Use original content directly
        content = section.content.strip()

        # Add any guidelines if this is a question
        if section.type == 'question' and self.config.guidelines:
            # Prepend relevant guidelines
            guidelines_text = self._extract_relevant_guidelines(section)
            if guidelines_text:
                content = f"{guidelines_text}\n\n{content}"

        return [
            {
                "role": "system",
                "content": content
            }
        ]

    def _extract_enum_values(self, content: str, field: str) -> List[str]:
        """Try to extract enum values from content."""
        import re

        # Look for patterns like:
        # "Options: Salaried, Self-employed, Business Owner"
        # "(Salaried / Self-employed / Business Owner)"
        # "salaried or self-employed"

        enum_patterns = [
            r'Options?:\s*(.+?)[\n\.]',
            r'\(([^)]+?/[^)]+?)\)',
            r'\(([^)]+?\bor\b[^)]+?)\)',
        ]

        for pattern in enum_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                # Extract and split
                values_text = match.group(1)
                # Split by comma, /, or 'or'
                values = re.split(r',|/|\bor\b', values_text)
                # Clean up
                values = [v.strip() for v in values if v.strip()]
                if values:
                    return values

        return []

    def _extract_relevant_guidelines(self, section: ParsedSection) -> str:
        """Extract guidelines relevant to this section."""
        # For now, just return first guideline if it exists
        # Could be smarter and match guidelines to section type
        if self.config.guidelines:
            guideline = self.config.guidelines[0]
            return guideline.content.strip()
        return ""

    def create_all_nodes(self) -> List[NodeConfig]:
        """
        Create NodeConfig objects for all sections in flow order.

        Returns:
            List of NodeConfig objects in flow execution order
        """
        nodes = []

        for section_id in self.config.flow_order:
            section = self.config.sections_by_id.get(section_id)
            if section:
                node = self.create_node_for_section(section)
                nodes.append(node)

        return nodes

    def get_node_by_section_id(self, section_id: str) -> NodeConfig:
        """Get node for a specific section ID."""
        section = self.config.sections_by_id.get(section_id)
        if section:
            return self.create_node_for_section(section)
        return None
