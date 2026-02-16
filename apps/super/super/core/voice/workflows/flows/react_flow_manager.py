"""
ReAct Flow Manager - Lightweight wrapper for Pipecat FlowManager.

This module provides a thin adapter layer between ConversationFlow (domain model)
and Pipecat's FlowManager (execution engine), enabling step-by-step conversation
flow execution with SharedQueue integration.

Key responsibilities:
- Convert ConversationFlow nodes to Pipecat NodeConfigs (one at a time)
- Integrate with SharedQueue for state management
- Track execution state and observations
- Delegate actual flow execution to Pipecat FlowManager
- Register dynamic node progression with LLM

Architecture:
    ConversationFlow → ReActFlowManager ← SharedQueue → Pipecat FlowManager

Integration Model (LLM-Driven):
    1. initialize_first_node() → registers get_next_step() function with LLM
    2. FlowManager executes first node → LLM processes task
    3. LLM calls get_next_step() function when ready to progress
    4. get_next_step() → identify_next_action() → checks SharedQueue + ConversationFlow
    5. Returns (result, next_node_config) tuple to FlowManager
    6. FlowManager automatically transitions to next node
    7. Repeat from step 2

This follows Pipecat Flows' function-driven pattern where:
- Node transitions happen via function return values, not direct calls
- LLM controls conversation flow by calling registered functions
- SharedQueue enables reactive behavior (PA → CA communication)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, TypedDict

if TYPE_CHECKING:
    from super.core.voice.workflows.flows.conversation_flow import (
        ConversationFlow,
        ExecutableNode,
    )
    from super.core.voice.workflows.shared_queue import SharedQueueManager

try:
    from pipecat_flows import FlowManager
except ImportError:
    # Fallback for development/testing
    FlowManager = object  # type: ignore

logger = logging.getLogger(__name__)


# ============================================================================
# Type Definitions
# ============================================================================


class NodeType(Enum):
    """Node types for ReAct pattern (future use)."""

    THINK = "think"
    ACT = "act"
    OBSERVE = "observe"


class NodeExecutionResult(TypedDict, total=False):
    """Result from executing a single node."""

    success: bool
    node_id: str
    node_name: str
    data: Dict[str, Any]
    error: Optional[str]


class FlowStatus(TypedDict):
    """Current status of flow execution."""

    mode: str  # "conversation" or "standard"
    has_flow: bool
    steps_executed: int
    current_step: Optional[str]
    is_complete: bool


class ObservationSummary(TypedDict):
    """Summary of observation state."""

    actions_taken: int
    collected_fields: Dict[str, Any]
    missing_fields: List[str]
    goals_completed: List[str]
    goals_pending: List[str]
    turn_count: int


# ============================================================================
# Exception Classes
# ============================================================================


class FlowManagerError(Exception):
    """Base exception for flow manager errors."""


class FlowNotInitializedError(FlowManagerError):
    """Raised when attempting to execute before initialization."""


class NodeConversionError(FlowManagerError):
    """Raised when node conversion fails."""


class NodeExecutionError(FlowManagerError):
    """Raised when node execution fails."""


# ============================================================================
# State Management
# ============================================================================


@dataclass
class ObservationState:
    """Tracks observations from actions and conversation state."""

    # Action history
    actions_taken: List[Dict[str, Any]] = field(default_factory=list)

    # Goal tracking
    current_goal_id: Optional[str] = None
    collected_fields: Dict[str, Any] = field(default_factory=dict)
    missing_fields: List[str] = field(default_factory=list)

    # Conversation state
    turn_count: int = 0
    last_user_message: str = ""
    last_bot_response: str = ""

    # Flow control
    goals_completed: List[str] = field(default_factory=list)
    goals_pending: List[str] = field(default_factory=list)

    def add_action(
        self, action_name: str, result: Any, success: bool = True
    ) -> None:
        """Record an action taken."""
        self.actions_taken.append(
            {
                "action": action_name,
                "result": result,
                "success": success,
                "turn": self.turn_count,
            }
        )

    def update_goal_progress(self, goal_id: str, fields: Dict[str, Any]) -> None:
        """Update collected fields for current goal."""
        self.current_goal_id = goal_id
        self.collected_fields.update(fields)

    def is_goal_complete(self, required_fields: List[str]) -> bool:
        """Check if all required fields are collected."""
        return all(field in self.collected_fields for field in required_fields)

    def complete_goal(self, goal_id: str) -> None:
        """Mark goal as completed."""
        if goal_id in self.goals_pending:
            self.goals_pending.remove(goal_id)
        if goal_id not in self.goals_completed:
            self.goals_completed.append(goal_id)

    def to_summary(self) -> ObservationSummary:
        """Generate summary for external consumption."""
        return {
            "actions_taken": len(self.actions_taken),
            "collected_fields": self.collected_fields.copy(),
            "missing_fields": self.missing_fields.copy(),
            "goals_completed": self.goals_completed.copy(),
            "goals_pending": self.goals_pending.copy(),
            "turn_count": self.turn_count,
        }


@dataclass
class FlowState:
    """Consolidated flow execution state."""

    observation: ObservationState
    mode: str = "standard"  # "conversation" or "standard"
    initialized: bool = False
    steps_executed: int = 0
    current_step_name: Optional[str] = None
    current_step_id: Optional[str] = None  # Track current node ID for completion


# ============================================================================
# ReActFlowManager - Main Class
# ============================================================================


class ReActFlowManager(FlowManager):  # type: ignore
    """
    Lightweight wrapper around Pipecat FlowManager for ConversationFlow execution.

    This class acts as an adapter between ConversationFlow (domain model) and
    Pipecat's FlowManager (execution engine). It handles:
    - Lazy node conversion (one at a time)
    - State tracking via ObservationState
    - Error handling and recovery
    - Step-by-step execution control

    The actual flow execution is delegated to Pipecat's FlowManager.
    """

    def __init__(
        self,
        conversation_flow: Optional[ConversationFlow] = None,
        shared_queue: Optional[SharedQueueManager] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Initialize ReActFlowManager.

        Args:
            conversation_flow: Optional ConversationFlow for queue-based execution
            shared_queue: Optional SharedQueueManager for state management
            *args: Positional arguments for FlowManager
            **kwargs: Keyword arguments for FlowManager
        """
        super().__init__(*args, **kwargs)

        # ConversationFlow integration
        self.conversation_flow = conversation_flow

        # SharedQueue integration
        self.shared_queue = shared_queue

        # State management
        self._state = FlowState(
            observation=ObservationState(),
            mode="conversation" if conversation_flow else "standard",
        )

        logger.info(
            f"ReActFlowManager initialized in {self._state.mode} mode "
            f"(SharedQueue: {'enabled' if shared_queue else 'disabled'})"
        )

    # ========================================================================
    # Public API - Initialization
    # ========================================================================

    async def initialize_first_node(self) -> None:
        """
        Initialize with ONLY the first node - no bulk conversion.

        This method:
        1. Ensures ConversationFlow is initialized
        2. Gets ONLY the first node
        3. Converts it to Pipecat NodeConfig
        4. Registers dynamic progression function with LLM
        5. Initializes the underlying FlowManager
        6. Updates SharedQueue with initial state

        Raises:
            FlowNotInitializedError: If no ConversationFlow is configured
            NodeConversionError: If first node conversion fails
        """
        if not self.conversation_flow:
            raise FlowNotInitializedError(
                "No ConversationFlow configured. "
                "Create ReActFlowManager with conversation_flow parameter."
            )

        # Ensure ConversationFlow is initialized
        if not self.conversation_flow._initialized:
            await self.conversation_flow.initialize()
            logger.debug("ConversationFlow initialized")

        # Get ONLY first node (no while loop)
        first_node = await self.conversation_flow.get_next_node()

        # print("first nodeeee" , first_node)
        if not first_node:
            logger.warning("ConversationFlow has no nodes")
            return

        # Convert to Pipecat NodeConfig
        try:
            node_config =await self._convert_to_pipecat_config(first_node)
        except Exception as e:
            raise NodeConversionError(
                f"Failed to convert first node {first_node.id}: {e}"
            ) from e

        # ✅ CRITICAL: Mark first node as IN_PROGRESS BEFORE registering with LLM
        # This prevents get_next_step() from returning the same node during initialization
        if self.shared_queue:
            from super.core.voice.workflows.shared_queue import StepStatus

            await self.shared_queue.update_plan_progress(
                first_node.id, StepStatus.IN_PROGRESS
            )
            await self.shared_queue.update_context(
                {
                    "current_node": first_node.name,
                    "current_step_id": first_node.id,
                    "user": self.shared_queue.conversation_id,
                }
            )

        # Mark as initialized in state
        self._state.initialized = True
        self._state.current_step_name = first_node.name
        self._state.current_step_id = first_node.id  # Track node ID for completion

        # Initialize underlying FlowManager with first node
        # ✅ Node config now includes progression function (Pipecat Flows pattern)
        # FlowManager will automatically register the function with LLM
        await self.initialize(node_config)

        logger.info(
            f"✅ Initialized with first node: {first_node.name} "
            f"(with node-specific progression function)"
        )

    # ========================================================================
    # DEPRECATED: Old global function approach (kept for reference)
    # ========================================================================
    # NOTE: These methods are deprecated in favor of node-specific functions
    # attached to each NodeConfig (see _create_node_progression_function)
    #
    # The old approach used a single global get_next_step() function.
    # The new approach (Pipecat Flows pattern) uses node-specific functions.
    # ========================================================================

    async def _register_progression_function(self) -> None:
        """
        DEPRECATED: Register global progression function with LLM.

        This method is deprecated. We now use node-specific progression functions
        attached to each NodeConfig, following the proper Pipecat Flows pattern.

        See _create_node_progression_function() for the new approach.
        """
        logger.warning(
            "DEPRECATED: _register_progression_function() is deprecated. "
            "Using node-specific functions instead."
        )

    async def _get_next_step_handler(
        self, _args: Dict[str, Any], _flow_manager: "ReActFlowManager"
    ) -> tuple[Dict[str, Any], Optional[Any]]:
        """
        DEPRECATED: Global LLM-callable function for dynamic node progression.

        This method is deprecated. We now use node-specific progression functions
        that are created in _create_node_progression_function() and attached to
        each NodeConfig.

        This follows the proper Pipecat Flows pattern where each node has its own
        functions that the LLM can call.
        """
        logger.warning(
            "DEPRECATED: _get_next_step_handler() called. "
            "Should be using node-specific progression functions instead."
        )
        return ({"status": "error", "error": "Deprecated function called"}, None)

    async def _handle_conversation_step_action(
        self, action: Any, flow_manager: "ReActFlowManager"
    ) -> tuple[Dict[str, Any], Optional[Any]]:
        """
        Handle CONVERSATION_STEP action type.

        Args:
            action: QueueAction with type CONVERSATION_STEP
            flow_manager: Reference to ReActFlowManager instance

        Returns:
            tuple[result, next_node_config]: Result dict and NodeConfig
        """
        # Get next node from action payload
        node = action.payload.get("node")
        if not node:
            return ({"status": "error", "error": "No node in payload"}, None)

        # Convert to Pipecat NodeConfig
        next_config = await flow_manager._convert_to_pipecat_config(node)

        # Update SharedQueue progress
        if flow_manager.shared_queue:
            from super.core.voice.workflows.shared_queue import StepStatus

            await flow_manager.shared_queue.update_plan_progress(
                node.id, StepStatus.IN_PROGRESS
            )

        # Update state with new node (previous node already marked complete in handler)
        flow_manager._state.steps_executed += 1
        flow_manager._state.current_step_name = node.name
        flow_manager._state.current_step_id = node.id  # ✅ Track new node ID

        logger.info(f"Progressing to next step: {node.name} (id={node.id})")

        # ✅ Return next node config - FlowManager handles transition
        return ({"status": "progressing", "step": node.name}, next_config)

    async def _handle_wait_for_processing_action(
        self, action: Any
    ) -> tuple[Dict[str, Any], Optional[Any]]:
        """
        Handle WAIT_FOR_PROCESSING action type.

        Args:
            action: QueueAction with type WAIT_FOR_PROCESSING

        Returns:
            tuple[result, None]: Result dict with filler message, no node transition
        """
        # PA is busy - return filler without transitioning
        message = action.payload.get("message", "Let me check on that...")
        logger.info(f"PA busy, using filler: {message}")

        # Queue filler message to speak
        # TODO: Integrate with Pipecat TTS
        return ({"status": "waiting", "filler": message}, None)

    async def _handle_send_response_action(
        self, action: Any, flow_manager: "ReActFlowManager"
    ) -> tuple[Dict[str, Any], Optional[Any]]:
        """
        Handle SEND_RESPONSE action type.

        Args:
            action: QueueAction with type SEND_RESPONSE
            flow_manager: Reference to ReActFlowManager instance

        Returns:
            tuple[result, None]: Result dict with response, no node transition
        """
        from super.core.voice.workflows.shared_queue import ActionStatus

        # PA sent direct response - speak it without transitioning
        response = action.payload.get("response", "")
        logger.info(f"PA response: {response}")

        # Add to conversation history
        if flow_manager.shared_queue:
            await flow_manager.shared_queue.add_turn(
                role="assistant", message=response, node_id=None
            )

            # Mark action as completed after CA executes it
            await flow_manager.shared_queue.update_action_status(
                action_id=action.id,
                status=ActionStatus.COMPLETED
            )

        # TODO: Queue response to TTS
        return ({"status": "responding", "response": response}, None)

    # ========================================================================
    # Public API - Dynamic Node Identification
    # ========================================================================

    async def identify_next_action(
        self, _user_input: Optional[str] = None
    ) -> Optional[Any]:
        """
        Identify next action based on ActionQueue and conversation state.

        Priority:
        1. Check SharedQueue for pending actions TO_COMMUNICATION
        2. If PA is busy, create filler action
        3. If none, get next node from ConversationFlow

        Args:
            user_input: Optional user input for context

        Returns:
            Next QueueAction to execute, or None if flow complete
        """
        if not self.shared_queue:
            # Fallback: just get next node
            return await self._get_next_node_action()

        from super.core.voice.workflows.shared_queue import ActionDirection

        # STEP 1: Check queue for pending actions to CA
        pending_actions = await self.shared_queue.get_pending_actions(
            direction=ActionDirection.TO_COMMUNICATION
        )

        if pending_actions:
            # Priority action from PA
            action = await self.shared_queue.pop_action(
                direction=ActionDirection.TO_COMMUNICATION
            )
            logger.info(f"Picked action from queue: {action.type.value}")
            return action

        # STEP 2: Check if PA is still processing
        processing_actions = await self.shared_queue.get_pending_actions(
            direction=ActionDirection.TO_PROCESSING
        )

        if processing_actions:
            # PA is busy - create filler action
            logger.info("PA busy, creating filler conversation")
            return await self._create_filler_action()

        # STEP 3: Get next node from ConversationFlow
        return await self._get_next_node_action()

    async def execute_action(
        self, action: Any, user_input: Optional[str] = None
    ) -> bool:
        """
        Execute an action from the queue.

        Actions can be:
        - CONVERSATION_STEP: Execute node from plan
        - WAIT_FOR_PROCESSING: Filler while PA works
        - SEND_RESPONSE: Direct response from PA

        Args:
            action: QueueAction to execute
            user_input: Optional user input

        Returns:
            True if action executed successfully
        """
        if not action:
            return False

        from super.core.voice.workflows.shared_queue import (
            ActionStatus,
            ActionType,
        )

        try:
            # Mark action as in-progress
            if self.shared_queue and hasattr(action, "id"):
                await self.shared_queue.update_action_status(
                    action.id, ActionStatus.IN_PROGRESS
                )

            # Execute based on action type
            if hasattr(action, "type"):
                if action.type == ActionType.CONVERSATION_STEP:
                    # Execute node from ConversationFlow
                    node = action.payload.get("node")
                    await self._execute_node_step(node, user_input)

                elif action.type == ActionType.WAIT_FOR_PROCESSING:
                    # Filler conversation
                    message = action.payload.get("message")
                    await self._execute_filler_step(message)

                elif action.type == ActionType.SEND_RESPONSE:
                    # Direct response from PA
                    response = action.payload.get("response")
                    await self._execute_response_step(response)

            # Mark action as completed
            if self.shared_queue and hasattr(action, "id"):
                await self.shared_queue.update_action_status(
                    action.id, ActionStatus.COMPLETED
                )

            return True

        except Exception as e:
            logger.error(f"Failed to execute action: {e}", exc_info=True)
            if self.shared_queue and hasattr(action, "id"):
                await self.shared_queue.update_action_status(
                    action.id, ActionStatus.FAILED, error=str(e)
                )
            return False

    async def step(self, user_input: Optional[str] = None) -> bool:
        """
        Execute one step of the conversation flow.

        This is the main entry point for CA's conversational loop.

        Flow:
        1. Observe ActionQueue
        2. Identify next action
        3. Execute action
        4. Update SharedQueue

        Args:
            user_input: Optional user input to process

        Returns:
            True if step executed, False if flow complete
        """
        # STEP 1: Identify next action
        action = await self.identify_next_action(user_input)

        if not action:
            logger.info("No more actions - conversation complete")
            return False

        # STEP 2: Execute action
        success = await self.execute_action(action, user_input)

        if not success:
            # Handle error via guardrails
            await self._handle_execution_error(action)

        # STEP 3: Update conversation history
        if self.shared_queue and user_input:
            node_id = (
                action.payload.get("node_id") if hasattr(action, "payload") else None
            )
            await self.shared_queue.add_turn(
                role="user", message=user_input, node_id=node_id
            )

        return True

    # ========================================================================
    # Public API - Execution
    # ========================================================================

    async def execute_next_step(self) -> bool:
        """
        Execute the next step from ConversationFlow.

        This is the main entry point for step-by-step execution. It:
        1. Gets the next node from ConversationFlow
        2. Converts it to Pipecat NodeConfig
        3. Executes via underlying FlowManager
        4. Updates state and marks node as completed

        Returns:
            True if a step was executed, False if flow is complete

        Raises:
            FlowNotInitializedError: If ConversationFlow not configured
            NodeExecutionError: If node execution fails
        """
        if not self.conversation_flow:
            raise FlowNotInitializedError(
                "No ConversationFlow configured. "
                "Call initialize_conversation_flow() first."
            )

        # Ensure flow is initialized
        if not self.conversation_flow._initialized:
            await self.conversation_flow.initialize()

        # Get next node
        next_node = await self.conversation_flow.get_next_node()
        if not next_node:
            logger.info("ConversationFlow completed - no more nodes")
            return False

        logger.info(
            f"Executing step: {next_node.name} (order: {next_node.order})"
        )

        try:
            # Execute the node
            result = await self._execute_single_node(next_node)

            # Mark as completed in ConversationFlow
            collected_data = result.get("data", {})
            await self.conversation_flow.mark_completed(
                next_node.id, collected_data
            )

            # Update state
            self._state.steps_executed += 1
            self._state.current_step_name = next_node.name
            self._update_observation_after_execution(next_node)

            return True

        except Exception as e:
            logger.error(
                f"Error executing node {next_node.id}: {e}", exc_info=True
            )

            # Handle error using ConversationFlow's error handling
            next_node_id = await self.conversation_flow.handle_error(
                next_node.id, e
            )

            if next_node_id == "general_conversation":
                logger.info("Falling back to general conversation mode")
                return False

            # Re-raise to let caller handle
            raise NodeExecutionError(
                f"Failed to execute node {next_node.id}"
            ) from e

    # ========================================================================
    # Public API - State Management
    # ========================================================================

    async def reset(self) -> None:
        """Reset state for new conversation."""
        self._state = FlowState(
            observation=ObservationState(),
            mode=self._state.mode,
        )
        if self.conversation_flow:
            await self.conversation_flow.initialize()
        logger.info("Flow state reset")

    def get_observation_summary(self) -> ObservationSummary:
        """Get current observation state summary."""
        return self._state.observation.to_summary()

    def get_flow_status(self) -> FlowStatus:
        """Get current flow status and progress."""
        if not self.conversation_flow:
            return {
                "mode": "standard",
                "has_flow": False,
                "steps_executed": 0,
                "current_step": None,
                "is_complete": True,
            }

        return {
            "mode": "conversation",
            "has_flow": True,
            "steps_executed": self._state.steps_executed,
            "current_step": self._state.current_step_name,
            "is_complete": not self.conversation_flow.has_next(),
        }

    # ========================================================================
    # Private Methods - SharedQueue Verification
    # ========================================================================

    async def verify_queue_push(
        self, action_type: Any, direction: Any, timeout: float = 2.0
    ) -> bool:
        """
        Verify that an action was successfully pushed to SharedQueue.

        Args:
            action_type: ActionType to verify
            direction: ActionDirection to check
            timeout: Maximum time to wait for verification (seconds)

        Returns:
            True if action is in queue, False otherwise
        """
        if not self.shared_queue:
            logger.warning("SharedQueue not available, cannot verify push")
            return False

        try:
            import asyncio

            start_time = asyncio.get_event_loop().time()

            while asyncio.get_event_loop().time() - start_time < timeout:
                # Check if action exists in queue
                pending_actions = await self.shared_queue.get_pending_actions(
                    direction=direction
                )

                # Verify action type matches
                for action in pending_actions:
                    if action.type == action_type:
                        logger.info(
                            f"✅ Verified: Action {action_type.value} found in {direction.value} queue"
                        )
                        return True

                await asyncio.sleep(0.1)

            logger.warning(
                f"⚠️ Verification timeout: Action {action_type.value} not found in {direction.value} queue after {timeout}s"
            )
            return False

        except Exception as e:
            logger.error(f"Error verifying queue push: {e}", exc_info=True)
            return False

    async def get_queue_status(self) -> Dict[str, Any]:
        """
        Get current status of SharedQueue for debugging.

        Returns:
            Dictionary with queue statistics
        """
        if not self.shared_queue:
            return {
                "enabled": False,
                "error": "SharedQueue not available"
            }

        try:
            from super.core.voice.workflows.shared_queue import ActionDirection

            to_communication = await self.shared_queue.get_pending_actions(
                direction=ActionDirection.TO_COMMUNICATION
            )
            to_processing = await self.shared_queue.get_pending_actions(
                direction=ActionDirection.TO_PROCESSING
            )

            status = {
                "enabled": True,
                "conversation_id": self.shared_queue.conversation_id,
                "to_communication_count": len(to_communication),
                "to_processing_count": len(to_processing),
                "to_communication_actions": [
                    {"type": a.type.value, "status": a.status.value} for a in to_communication
                ],
                "to_processing_actions": [
                    {"type": a.type.value, "status": a.status.value} for a in to_processing
                ],
            }

            logger.debug(
                f"📊 Queue Status: CA={status['to_communication_count']}, PA={status['to_processing_count']}"
            )
            return status

        except Exception as e:
            logger.error(f"Error getting queue status: {e}", exc_info=True)
            return {
                "enabled": True,
                "error": str(e)
            }

    # ========================================================================
    # Private Methods - Dynamic Node Identification Helpers
    # ========================================================================

    async def _get_next_node_action(self) -> Optional[Any]:
        """
        Get next node from ConversationFlow and wrap as QueueAction.

        Returns:
            QueueAction wrapping the next node, or None if no more nodes
        """
        if not self.conversation_flow:
            return None

        from super.core.voice.workflows.shared_queue import (
            ActionDirection,
            ActionStatus,
            ActionType,
            QueueAction,
        )
        import uuid

        next_node = await self.conversation_flow.get_next_node()
        if not next_node:
            return None

        return QueueAction(
            id=str(uuid.uuid4()),
            type=ActionType.CONVERSATION_STEP,
            direction=ActionDirection.TO_COMMUNICATION,
            status=ActionStatus.PENDING,
            payload={
                "node": next_node,
                "node_id": next_node.id,
                "content": next_node.content,
            },
        )

    async def _create_filler_action(self) -> Any:
        """
        Create filler action for when PA is busy processing.

        Returns:
            QueueAction for filler conversation
        """
        from super.core.voice.workflows.shared_queue import (
            ActionDirection,
            ActionStatus,
            ActionType,
            QueueAction,
        )
        import uuid

        return QueueAction(
            id=str(uuid.uuid4()),
            type=ActionType.WAIT_FOR_PROCESSING,
            direction=ActionDirection.TO_COMMUNICATION,
            status=ActionStatus.PENDING,
            payload={
                "message": "Let me check on that for you. In the meantime, is there anything else I can help with?"
            },
        )

    async def _execute_node_step(
        self, node: ExecutableNode, _user_input: Optional[str] = None
    ) -> None:
        """
        Execute a conversation step node.

        Args:
            node: ExecutableNode to execute
            user_input: Optional user input
        """
        if not node:
            return

        # Execute the node via existing method
        result = await self._execute_single_node(node)

        # Mark as completed in ConversationFlow
        if self.conversation_flow:
            collected_data = result.get("data", {})
            await self.conversation_flow.mark_completed(node.id, collected_data)

        # Update SharedQueue plan progress
        if self.shared_queue:
            from super.core.voice.workflows.shared_queue import StepStatus

            await self.shared_queue.update_plan_progress(
                node.id, StepStatus.COMPLETED
            )

        # Update state
        self._state.steps_executed += 1
        self._state.current_step_name = node.name
        self._state.current_step_id = node.id  # ✅ Track node ID
        self._update_observation_after_execution(node)

        logger.info(f"Completed conversation step: {node.name} (id={node.id})")

    async def _execute_filler_step(self, message: str) -> None:
        """
        Execute filler conversation while PA works.

        Args:
            message: Filler message to speak
        """
        # TODO: Integrate with Pipecat to speak the filler message
        logger.info(f"Filler conversation: {message}")

        # For now, just log it
        # In full implementation, this would use Pipecat's TTS

    async def _execute_response_step(self, response: str) -> None:
        """
        Execute direct response from PA.

        Args:
            response: Response text from PA
        """
        # TODO: Integrate with Pipecat to speak the response
        logger.info(f"PA response: {response}")

        # Add to conversation history
        if self.shared_queue:
            await self.shared_queue.add_turn(
                role="assistant", message=response, node_id=None
            )

    async def _handle_execution_error(self, action: Any) -> None:
        """
        Handle execution errors gracefully.

        Fallback chain:
        1. Try next node in plan
        2. Use general conversation
        3. Handover to human

        Args:
            action: The action that failed
        """
        logger.error(f"Handling error for action: {action}")

        from super.core.voice.workflows.shared_queue import (
            ActionDirection,
            ActionType,
        )

        # Push fallback action to queue
        if self.shared_queue:
            await self.shared_queue.push_action(
                action_type=ActionType.CONVERSATION_STEP,
                direction=ActionDirection.TO_COMMUNICATION,
                payload={
                    "message": "I'm not sure about that. Let me help with something else.",
                    "fallback": True,
                },
            )

    # ========================================================================
    # Private Methods - Node Execution
    # ========================================================================

    async def _execute_single_node(
        self, node: ExecutableNode
    ) -> NodeExecutionResult:
        """
        Execute a single ExecutableNode.

        NOTE: In the new LLM-driven architecture, node execution happens
        automatically via FlowManager when get_next_step() returns node config.
        This method is kept for backward compatibility with execute_next_step().

        This orchestrates the execution by:
        1. Converting node to Pipecat format
        2. Transitioning via set_node_from_config (Pipecat's public API)
        3. Returning result

        Args:
            node: ExecutableNode to execute

        Returns:
            Execution result with success status and data

        Raises:
            NodeConversionError: If conversion fails
            NodeExecutionError: If execution fails
        """
        # Step 1: Convert to Pipecat NodeConfig
        try:
            node_config =await  self._convert_to_pipecat_config(node)
        except Exception as e:
            raise NodeConversionError(
                f"Failed to convert node {node.id}: {e}"
            ) from e

        # Step 2: Transition using Pipecat's public API
        # ✅ FIXED: Use set_node_from_config() instead of internal _set_node()
        try:
            await self.set_node_from_config(node_config)
        except Exception as e:
            raise NodeExecutionError(
                f"Failed to execute node {node.id}"
            ) from e

        # Step 3: Return result
        return {
            "success": True,
            "node_id": node.id,
            "node_name": node.name,
            "data": {},
            "error": None,
        }

    async def _convert_to_pipecat_config(self, node: ExecutableNode) -> Any:
        """
        Convert ExecutableNode to Pipecat NodeConfig with functions.

        This follows the Pipecat Flows pattern:
        1. Create node-specific progression function
        2. Get base NodeConfig from ExecutableNode with function included
        3. NodeConfig includes function that LLM can call for progression

        Args:
            node: ExecutableNode to convert

        Returns:
            Pipecat NodeConfig object with progression function

        Raises:
            NodeConversionError: If conversion fails
        """
        from super.core.voice.workflows.flows.conversation_flow import (
            executable_node_to_pipecat_config,
        )

        # Step 1: Create node-specific progression function
        # This follows Pipecat Flows pattern where each node has functions
        progression_fn = self._create_node_progression_function(node)

        # Step 2: Create document retrieval function (delegates to PassiveAgent)
        retrieve_docs_fn = self._create_document_retrieval_function(node)

        # Step 3: Get base NodeConfig (already has functions from node's actions)
        node_config = executable_node_to_pipecat_config(node)
        if not node_config:
            raise NodeConversionError(
                f"Conversion returned None for node {node.id}"
            )

        # Step 4: Merge all functions (progression + retrieval + existing)
        # NodeConfig is a TypedDict (plain dict at runtime)
        existing_functions = node_config.get('functions') or []
        all_functions = list(existing_functions) + [progression_fn,retrieve_docs_fn]

        # Create new NodeConfig dict with updated functions
        # Use dict unpacking to copy all fields and override functions
        from pipecat_flows.types import ContextStrategyConfig, ContextStrategy

        # Extract summary prompt string from task_messages
        # task_messages is a list of dicts: [{"role": "user", "content": "..."}]
        summary_prompt_text = "Summarize the conversation so far, focusing on key information gathered and actions taken."
        task_messages = node_config.get("task_messages", [])
        if task_messages and isinstance(task_messages, list) and len(task_messages) > 0:
            first_msg = task_messages[0]
            if isinstance(first_msg, dict) and "content" in first_msg:
                summary_prompt_text = first_msg["content"]
        from super.core.voice.prompts.summary import context_update_summary
        from super.core.voice.workflows.shared_queue import ActionDirection, ActionType, ActionStatus


        action = await self.shared_queue.pop_action(
            ActionDirection.TO_COMMUNICATION
        )

        if action:
            await self.shared_queue.update_action_status(
                action_id=action.id,
                status=ActionStatus.COMPLETED,
            )

        updated_config = {
            **node_config,  # Copy all existing fields
            'functions': all_functions,  # Override functions with merged list
            'context_strategy': ContextStrategyConfig(
                strategy=ContextStrategy.RESET_WITH_SUMMARY,
                summary_prompt=context_update_summary+summary_prompt_text + str(action),
                # summary_prompt=context_update_summary+summary_prompt_text,

            )
        }

        return updated_config

    def _create_node_progression_function(self, node: ExecutableNode) -> Any:
        """
        Create a progression function specific to this node.

        This function follows Pipecat Flows pattern:
        - LLM calls this function when node task is complete
        - Function marks current node as complete
        - Function gets next node and returns its config
        - FlowManager automatically transitions

        Args:
            node: ExecutableNode to create function for

        Returns:
            Function that LLM can call for progression
        """
        async def progress_from_node(flow_manager) -> tuple[Dict[str, Any], Optional[Any]]:  # noqa: ARG001
            """
            Progress from current node to next.

            This is registered with the LLM and called when ready to progress.
            Pipecat requires the first parameter to be named 'flow_manager'.

            Args:
                flow_manager: FlowManager instance (required by Pipecat, intentionally unused)
            """
            try:
                # Mark current node as COMPLETED
                logger.info(f"🎯 LLM called progression function for node {node.id} ({node.name})!")
                logger.info(f"   Marking node as COMPLETED and fetching next node...")

                if self.conversation_flow:
                    await self.conversation_flow.mark_completed(node.id, {})

                if self.shared_queue:
                    from super.core.voice.workflows.shared_queue import StepStatus
                    await self.shared_queue.update_plan_progress(
                        node.id, StepStatus.COMPLETED
                    )

                # Get next action (checks SharedQueue + ConversationFlow)
                action = await self.identify_next_action()

                if not action:
                    logger.info("No more nodes - conversation complete")
                    return ({"status": "complete"}, None)

                # Delegate to action handlers (strategy pattern)
                from super.core.voice.workflows.shared_queue import ActionType

                if action.type == ActionType.CONVERSATION_STEP:
                    return await self._handle_conversation_step_action(action, self)
                elif action.type == ActionType.WAIT_FOR_PROCESSING:
                    return await self._handle_wait_for_processing_action(action)
                elif action.type == ActionType.SEND_RESPONSE:
                    return await self._handle_send_response_action(action, self)
                else:
                    logger.warning(f"Unknown action type: {action.type}")
                    return ({"status": "error", "error": "Unknown action type"}, None)

            except Exception as e:
                logger.error(f"Error in node progression: {e}", exc_info=True)
                return ({"status": "error", "error": str(e)}, None)

        # Set function name for LLM (e.g., "complete_greeting_step")
        # Import sanitization function from conversation_flow
        from super.core.voice.workflows.flows.conversation_flow import _sanitize_function_name
        sanitized_name = _sanitize_function_name(node.name)
        progress_from_node.__name__ = f"complete_{sanitized_name}_step"

        return progress_from_node

    def _create_document_retrieval_function(self, node: ExecutableNode) -> Any:
        """
        Create a document retrieval function that delegates to PassiveAgent.

        This function allows the LLM to request document retrieval during
        conversation flow execution. The request is pushed to SharedQueue
        and processed by PassiveAgent in the background.

        Args:
            node: ExecutableNode to create function for

        Returns:
            FlowsFunctionSchema that LLM can call to retrieve documents
        """
        async def retrieve_documents( query: str) -> tuple[str, None]:  # noqa: ARG001
            """
            Retrieve documents via PassiveAgent (non-blocking).

            This function delegates document retrieval to PassiveAgent and returns
            immediately, allowing the conversation to continue. The LLM can check
            back later for results by calling this function again.

            Args:
                flow_manager: FlowManager instance (required by Pipecat)
                query: Search query for document retrieval

            Returns:
                tuple[result, None]: Status message or retrieved documents, no node transition
            """

            if not query:
                logger.warning("retrieve_documents called with empty query")
                return ("No query provided", None)

            if not self.shared_queue:
                logger.warning("SharedQueue not available, cannot delegate to PassiveAgent")
                return ("Document retrieval not available", None)

            try:
                from super.core.voice.workflows.shared_queue import ActionDirection, ActionType, ActionStatus

                # STEP 1: Check if there's already a response from PA waiting
                response_action = await self.shared_queue.pop_action(
                    direction=ActionDirection.TO_COMMUNICATION
                )

                if response_action and response_action.type == ActionType.SEND_RESPONSE:
                    result = response_action.payload.get("response", "")
                    print(f"📥 LLM←PA: Received documents ({len(str(result))} chars)")

                    # Mark action as completed
                    await self.shared_queue.update_action_status(
                        response_action.id,
                        ActionStatus.COMPLETED
                    )

                    await self.shared_queue.push_action(
                        action_type=ActionType.PROCESS_USER_INPUT,
                        direction=ActionDirection.TO_PROCESSING,
                        payload={"task": query}
                    )


                    return (str(result), None)

                # STEP 2: No response yet, push new task to PA (non-blocking)
                print(f"📤 LLM→PA: Delegating doc retrieval for query: '{query}...'")

                await self.shared_queue.push_action(
                    action_type=ActionType.PROCESS_USER_INPUT,
                    direction=ActionDirection.TO_PROCESSING,
                    payload={"task": query}
                )

                # STEP 3: Return immediately - don't wait for PA
                return (
                    "Document retrieval request sent to background agent. "
                    "Continue the conversation naturally while I fetch the information.",
                    None
                )

            except Exception as e:
                logger.error(f"Error in retrieve_documents: {e}", exc_info=True)
                return (f"Error retrieving documents: {str(e)}", None)

        # Wrap in FlowsFunctionSchema so LLM knows when to call it
        try:
            from pipecat_flows import FlowsFunctionSchema

            return FlowsFunctionSchema(
                name="retrieve_documents",
                handler=retrieve_documents,
                description=(
                    "Search knowledge base and retrieve relevant documents to answer user questions. "
                    "Call this function BEFORE responding when you need information you don't have. "
                    "The function returns relevant context that you MUST use to formulate your answer. "
                    "After calling this function, use the returned information to provide a complete response to the user."
                ),
                properties={
                    "query": {
                        "type": "string",
                        "description": "The search query or question to find relevant documents for. Be specific and include key terms."
                    }
                },
                required=["query"]
            )
        except ImportError:
            # Fallback: return raw function (won't be called by LLM)
            logger.warning("FlowsFunctionSchema not available, retrieve_documents won't be callable by LLM")
            return retrieve_documents

    def _register_node_config(self, node_config: Any) -> None:
        """
        Register NodeConfig with FlowManager's internal tracking.

        This ensures Pipecat can find the node when _set_node is called.

        Args:
            node_config: Pipecat NodeConfig to register
        """
        # Initialize node configs dict if needed
        if not hasattr(self, "_node_configs"):
            self._node_configs: Dict[str, Any] = {}

        self._node_configs[node_config.name] = node_config

        # Update nodes list if FlowManager has one
        if hasattr(self, "nodes") and isinstance(self.nodes, list):
            # Check if node already exists
            existing = next(
                (n for n in self.nodes if n.name == node_config.name), None
            )
            if not existing:
                self.nodes.append(node_config)

        logger.debug(f"Registered node: {node_config.name}")

    def _update_observation_after_execution(self, node: ExecutableNode) -> None:
        """
        Update observation state after node execution.

        Args:
            node: ExecutableNode that was executed
        """
        self._state.observation.turn_count += 1
        self._state.observation.last_bot_response = node.content
        logger.debug(f"Updated observations after {node.name}")


# ============================================================================
# Factory Functions
# ============================================================================


def create_conversation_flow_manager(
    conversation_flow: ConversationFlow,
    shared_queue: Optional[SharedQueueManager] = None,
    **kwargs: Any,
) -> ReActFlowManager:
    """
    Factory function to create ReActFlowManager for ConversationFlow mode.

    Args:
        conversation_flow: ConversationFlow instance
        shared_queue: Optional SharedQueueManager for state management
        **kwargs: Additional arguments for FlowManager

    Returns:
        Configured ReActFlowManager instance

    Raises:
        ValueError: If conversation_flow is None
    """
    if not conversation_flow:
        raise ValueError("conversation_flow is required")

    return ReActFlowManager(
        conversation_flow=conversation_flow, shared_queue=shared_queue, **kwargs
    )


def create_standard_flow_manager(**kwargs: Any) -> ReActFlowManager:
    """
    Factory function to create ReActFlowManager for standard mode.

    Args:
        **kwargs: Arguments for FlowManager

    Returns:
        Configured ReActFlowManager instance
    """
    return ReActFlowManager(conversation_flow=None, **kwargs)
