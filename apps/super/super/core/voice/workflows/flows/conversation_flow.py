"""
ConversationFlow - Queue-based manager for conversation steps.

This module provides a queue-based conversation flow manager that integrates
with Pipecat's FlowManager and works with ConversationPlan from pydantic_ai_section_parser.

Architecture:
    ConversationPlan → ConversationFlow (queue) → ReActFlowManager (execution)

Key Features:
    - Sequential step execution with queue management
    - Dynamic instruction injection into node prompts
    - Async-compatible with Pipecat flows
    - Support for dynamic node addition
    - Graceful error handling with fallback

Author: AI Senior Architect
Date: 2025-11-15
"""

from typing import Dict, List, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum
import logging

if TYPE_CHECKING:
    from pipecat_flows import NodeConfig, FlowsFunctionSchema

try:
    from pipecat_flows import NodeConfig, FlowsFunctionSchema
except ImportError:
    # Fallback for development
    NodeConfig = object  # type: ignore
    FlowsFunctionSchema = object  # type: ignore

from super.core.voice.workflows.flows.pydantic_ai_section_parser import (
    ConversationPlan,
    StepModel,
    InstructionModel,
    InstructionType,
    ActionModel,
    GuardrailModel,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Type Definitions
# =============================================================================


class FlowStatus(str, Enum):
    """Status of the conversation flow"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"


class FallbackMode(str, Enum):
    """Fallback behavior when a step fails or is missing"""

    NEXT_STEP = "next_step"  # Continue to next step in queue
    GENERAL_CONVERSATION = "general_conversation"  # Fall back to general mode
    END_FLOW = "end_flow"  # End the conversation


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class ExecutableNode:
    """
    Minimal executable node representation.

    This bridges ConversationPlan steps to Pipecat NodeConfig.
    """

    id: str
    name: str
    content: str
    order: int
    node_type: str = "step"  # step, action, question
    next_node_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Dynamic context (injected per execution)
    instructions_context: str = ""
    identity_context: str = ""
    guidelines_context: str = ""

    # Fields to collect (if applicable)
    fields: List[Dict[str, Any]] = field(default_factory=list)

    # Conditional branches (if applicable)
    conditional_branches: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class FlowState:
    """Tracks the current state of the conversation flow"""

    current_node_id: Optional[str] = None
    current_node_order: int = 0
    completed_node_ids: List[str] = field(default_factory=list)
    collected_data: Dict[str, Any] = field(default_factory=dict)
    status: FlowStatus = FlowStatus.PENDING
    error_message: Optional[str] = None


# =============================================================================
# ConversationFlow - Main Queue Manager
# =============================================================================


class ConversationFlow:
    """
    Queue manager for conversation steps.

    Manages the flow of conversation by:
    1. Converting ConversationPlan steps to executable nodes
    2. Maintaining a queue of nodes to execute
    3. Tracking current state and completed nodes
    4. Dynamically injecting instructions into each node
    5. Providing async-compatible interface for Pipecat

    Example:
        >>> plan = parse_conversation_plan(system_prompt)
        >>> flow = ConversationFlow(plan)
        >>> await flow.initialize()
        >>> node = await flow.get_next_node()
        >>> # Execute node...
        >>> await flow.mark_completed(node.id)
    """

    def __init__(
        self,
        plan: ConversationPlan,
        fallback_mode: FallbackMode = FallbackMode.GENERAL_CONVERSATION,
    ):
        """
        Initialize ConversationFlow from a ConversationPlan.

        Args:
            plan: Parsed ConversationPlan with instructions, steps, etc.
            fallback_mode: What to do when a step fails or is missing
        """
        self.plan = plan
        self.fallback_mode = fallback_mode

        # Queue and state
        self.queue: List[ExecutableNode] = []
        self.state = FlowState()

        # Cached contexts (built from instructions)
        self._instructions_context: str = ""
        self._identity_context: str = ""
        self._guidelines_context: str = ""
        self._style_context: str = ""

        # Node lookup
        self._nodes_by_id: Dict[str, ExecutableNode] = {}
        self._nodes_by_order: Dict[int, ExecutableNode] = {}

        # Initialized flag
        self._initialized = False

    async def initialize(self) -> None:
        """
        Initialize the flow (async).

        Builds the queue and prepares contexts.
        This must be called before using the flow.
        """
        if self._initialized:
            return

        # Build instruction contexts
        self._build_instruction_contexts()

        # Initialize queue from ConversationPlan steps
        await self._initialize_queue()

        self._initialized = True
        self.state.status = FlowStatus.IN_PROGRESS

        logger.info(
            f"ConversationFlow initialized with {len(self.queue)} nodes"
        )

    def _build_instruction_contexts(self) -> None:
        """
        Build context strings from ConversationPlan instructions.

        Instructions are categorized by type and formatted for injection.
        """
        instructions_by_type: Dict[InstructionType, List[InstructionModel]] = {}

        for instruction in self.plan.instructions:
            if instruction.type not in instructions_by_type:
                instructions_by_type[instruction.type] = []
            instructions_by_type[instruction.type].append(instruction)

        # Build identity context
        if InstructionType.IDENTITY in instructions_by_type:
            identity_parts = [
                inst.content for inst in instructions_by_type[InstructionType.IDENTITY]
            ]
            self._identity_context = "\n\n".join(identity_parts)

        # Build guidelines context
        if InstructionType.GUIDELINE in instructions_by_type:
            guideline_parts = [
                inst.content
                for inst in instructions_by_type[InstructionType.GUIDELINE]
            ]
            self._guidelines_context = "\n\n".join(guideline_parts)

        # Build style context
        if InstructionType.STYLE in instructions_by_type:
            style_parts = [
                inst.content for inst in instructions_by_type[InstructionType.STYLE]
            ]
            self._style_context = "\n\n".join(style_parts)

        # Build system/general instructions
        system_instructions = []
        for inst_type in [InstructionType.SYSTEM, InstructionType.PERSONALITY, InstructionType.TONE]:
            if inst_type in instructions_by_type:
                system_instructions.extend([
                    inst.content for inst in instructions_by_type[inst_type]
                ])

        self._instructions_context = "\n\n".join(system_instructions)

    async def _initialize_queue(self) -> None:
        """
        Initialize queue from ConversationPlan steps.

        Converts StepModel objects to ExecutableNode objects and builds
        the execution queue in order.
        """
        # Sort steps by order
        sorted_steps = sorted(self.plan.steps, key=lambda s: s.order)

        for step in sorted_steps:
            node = self._step_to_executable_node(step)
            self.queue.append(node)
            self._nodes_by_id[node.id] = node
            self._nodes_by_order[node.order] = node

        logger.debug(f"Initialized queue with {len(self.queue)} nodes")

    def _step_to_executable_node(self, step: StepModel) -> ExecutableNode:
        """
        Convert a StepModel to an ExecutableNode.

        Args:
            step: StepModel from ConversationPlan

        Returns:
            ExecutableNode ready for execution
        """
        # Extract fields if any
        fields = []
        for field_schema in step.fields:
            fields.append({
                "name": field_schema.name,
                "type": field_schema.field_type,
                "description": field_schema.description,
                "required": field_schema.required,
                "prompt_text": field_schema.prompt_text,
            })

        # Extract conditional branches if any
        branches = []
        for branch in step.conditional_branches:
            branches.append({
                "condition": branch.condition,
                "target_step_id": branch.target_step_id,
                "condition_type": branch.condition_type,
            })

        return ExecutableNode(
            id=step.id,
            name=step.name,
            content=step.content,
            order=step.order,
            node_type="step",
            next_node_id=step.next_step_id,
            fields=fields,
            conditional_branches=branches,
            metadata={
                "step_type": step.type,
                "prompt_template": step.prompt_template,
                "validation_rules": step.validation_rules,
                "max_retries": step.max_retries,
            },
            # Inject contexts
            instructions_context=self._instructions_context,
            identity_context=self._identity_context,
            guidelines_context=self._guidelines_context,
        )

    async def get_next_node(self) -> Optional[ExecutableNode]:
        """
        Get the next node to execute from the queue.

        Returns:
            Next ExecutableNode or None if flow is complete
        """
        if not self._initialized:
            await self.initialize()

        # Check if flow is complete
        if self.is_complete():
            return None

        # If we have a current node in state, continue from there
        if self.state.current_node_id:
            current_node = self._nodes_by_id.get(self.state.current_node_id)
            if current_node and current_node.id not in self.state.completed_node_ids:
                return current_node

        # Otherwise, get the next uncompleted node from queue
        for node in self.queue:
            if node.id not in self.state.completed_node_ids:
                self.state.current_node_id = node.id
                self.state.current_node_order = node.order
                return node

        # No more nodes
        return None

    async def mark_completed(
        self, node_id: str, collected_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Mark a node as completed and update state.

        Args:
            node_id: ID of the completed node
            collected_data: Optional data collected during node execution
        """
        if node_id not in self._nodes_by_id:
            logger.warning(f"Attempted to mark unknown node as completed: {node_id}")
            return

        # Mark as completed
        if node_id not in self.state.completed_node_ids:
            self.state.completed_node_ids.append(node_id)

        # Update collected data
        if collected_data:
            self.state.collected_data.update(collected_data)

        # Update current node to None (will be set by get_next_node)
        self.state.current_node_id = None

        # Check if flow is complete
        if self.is_complete():
            self.state.status = FlowStatus.COMPLETED
            logger.info("ConversationFlow completed")

    async def add_node(
        self, node: ExecutableNode, position: Optional[int] = None
    ) -> None:
        """
        Dynamically add a node to the queue.

        Args:
            node: ExecutableNode to add
            position: Optional position in queue (None = append to end)
        """
        # Inject contexts into the new node
        node.instructions_context = self._instructions_context
        node.identity_context = self._identity_context
        node.guidelines_context = self._guidelines_context

        # Add to lookup
        self._nodes_by_id[node.id] = node
        self._nodes_by_order[node.order] = node

        # Add to queue
        if position is None:
            self.queue.append(node)
        else:
            self.queue.insert(position, node)

        logger.info(f"Added node '{node.name}' to flow at position {position}")

    def is_complete(self) -> bool:
        """
        Check if the conversation flow is complete.

        Returns:
            True if all nodes in queue are completed
        """
        return len(self.state.completed_node_ids) >= len(self.queue)

    def get_node_by_id(self, node_id: str) -> Optional[ExecutableNode]:
        """Get a node by its ID"""
        return self._nodes_by_id.get(node_id)

    def get_node_by_order(self, order: int) -> Optional[ExecutableNode]:
        """Get a node by its order"""
        return self._nodes_by_order.get(order)

    async def handle_error(self, node_id: str, error: Exception) -> Optional[str]:
        """
        Handle error during node execution.

        Args:
            node_id: ID of the node that errored
            error: The exception that occurred

        Returns:
            Next node ID to execute, or None to end flow
        """
        logger.error(f"Error in node {node_id}: {error}")
        self.state.error_message = str(error)

        # Handle based on fallback mode
        if self.fallback_mode == FallbackMode.NEXT_STEP:
            # Mark current as completed (despite error) and move to next
            await self.mark_completed(node_id)
            next_node = await self.get_next_node()
            return next_node.id if next_node else None

        elif self.fallback_mode == FallbackMode.GENERAL_CONVERSATION:
            # Return a special ID for general conversation mode
            return "general_conversation"

        else:  # FallbackMode.END_FLOW
            self.state.status = FlowStatus.ERROR
            return None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert flow state to dictionary for serialization.

        Returns:
            Dictionary representation of flow state
        """
        return {
            "status": self.state.status.value,
            "current_node_id": self.state.current_node_id,
            "current_node_order": self.state.current_node_order,
            "completed_nodes": self.state.completed_node_ids,
            "collected_data": self.state.collected_data,
            "total_nodes": len(self.queue),
            "error_message": self.state.error_message,
        }

    def get_progress(self) -> Dict[str, Any]:
        """
        Get progress information.

        Returns:
            Dictionary with progress metrics
        """
        total = len(self.queue)
        completed = len(self.state.completed_node_ids)

        return {
            "total_steps": total,
            "completed_steps": completed,
            "remaining_steps": total - completed,
            "progress_percentage": (completed / total * 100) if total > 0 else 0,
            "current_step": self.state.current_node_order,
            "status": self.state.status.value,
        }


# =============================================================================
# Helper Functions
# =============================================================================


async def create_flow_from_plan(
    plan: ConversationPlan,
    fallback_mode: FallbackMode = FallbackMode.GENERAL_CONVERSATION,
) -> ConversationFlow:
    """
    Create and initialize a ConversationFlow from a ConversationPlan.

    Args:
        plan: Parsed ConversationPlan
        fallback_mode: Fallback behavior on errors

    Returns:
        Initialized ConversationFlow ready for execution
    """
    flow = ConversationFlow(plan, fallback_mode)
    await flow.initialize()
    return flow


# =============================================================================
# NodeConfig Converter
# =============================================================================


def _sanitize_function_name(name: str) -> str:
    """
    Sanitize a string to be a valid OpenAI function name.

    OpenAI requires function names to match: ^[a-zA-Z0-9_-]+$
    (only letters, numbers, underscores, and hyphens)

    Args:
        name: Raw name string (may contain spaces, special chars, etc.)

    Returns:
        Sanitized name suitable for OpenAI function names
    """
    import re
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', name.lower())
    # Collapse consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores
    return sanitized.strip('_')


def executable_node_to_pipecat_config(node: ExecutableNode) -> "NodeConfig":
    """
    Convert ExecutableNode to Pipecat NodeConfig.

    This function builds a NodeConfig that Pipecat can execute, with
    dynamically injected instructions and context.

    Args:
        node: ExecutableNode to convert

    Returns:
        Pipecat NodeConfig ready for execution
    """
    # Build role messages (system context)
    role_messages = []

    # Add identity
    if node.identity_context:
        role_messages.append({
            "role": "system",
            "content": f"## Identity\n{node.identity_context}"
        })

    # Add guidelines
    if node.guidelines_context:
        role_messages.append({
            "role": "system",
            "content": f"## Guidelines\n{node.guidelines_context}"
        })

    # Add system instructions
    if node.instructions_context:
        role_messages.append({
            "role": "system",
            "content": f"## Instructions\n{node.instructions_context}"
        })

    # Build task messages (what to do in this step)
    task_messages = []

    # Main step content
    task_content = f"## Current Step: {node.name}\n\n{node.content}"

    # Add field collection instructions if applicable
    if node.fields:
        field_names = [f["name"] for f in node.fields]
        task_content += f"\n\nCollect the following information: {', '.join(field_names)}"

    # Add progression instruction (CRITICAL for node switching)
    sanitized_name = _sanitize_function_name(node.name)
    progression_function_name = f"complete_{sanitized_name}_step"
    task_content += f"\n\n## When Complete\nOnce you have finished this step's objective, call the `{progression_function_name}()` function to progress to the next step."

    task_messages.append({
        "role": "user",
        "content": task_content
    })

    # Build functions if fields need to be collected
    functions: List["FlowsFunctionSchema"] = []
    if node.fields:
        # Create a function schema for field collection
        from pipecat_flows import FlowsFunctionSchema

        properties = {}
        required = []

        for field in node.fields:
            properties[field["name"]] = {
                "type": field["type"],
                "description": field["description"]
            }
            if field["required"]:
                required.append(field["name"])

        # Create a no-op handler for field collection
        async def collect_fields(args, flow_manager):
            """Collect fields - this is a placeholder handler."""
            return args, None

        # Sanitize function name for OpenAI
        collect_fn_name = _sanitize_function_name(node.name)

        function_schema = FlowsFunctionSchema(
            name=f"collect_{collect_fn_name}",
            handler=collect_fields,
            description=f"Collect information for {node.name}",
            properties=properties,
            required=required
        )
        functions.append(function_schema)

    # Create NodeConfig
    try:
        from pipecat_flows import NodeConfig

        # Sanitize NodeConfig name as well (for consistency)
        node_config_name = _sanitize_function_name(node.name)

        return NodeConfig(
            name=node_config_name,
            role_messages=role_messages,
            task_messages=task_messages,
            functions=functions if functions else None,
            respond_immediately=True,
        )
    except ImportError:
        logger.error("pipecat_flows not available, cannot create NodeConfig")
        raise


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    print("ConversationFlow - Queue Manager for Conversation Steps")
    print("=" * 60)
    print()
    print("This module provides:")
    print("✓ Queue-based conversation flow management")
    print("✓ Dynamic instruction injection")
    print("✓ Async-compatible with Pipecat")
    print("✓ Error handling with fallback modes")
    print("✓ Progress tracking")
    print()
    print("Usage:")
    print(">>> plan = parse_conversation_plan(system_prompt)")
    print(">>> flow = await create_flow_from_plan(plan)")
    print(">>> node = await flow.get_next_node()")
    print(">>> # Execute node...")
    print(">>> await flow.mark_completed(node.id)")
    print()
