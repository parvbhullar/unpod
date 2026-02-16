"""
SharedQueueManager - Central state management for conversational agents.

This module provides a thread-safe, Redis-backed queue manager for managing
conversation state, action queues, and inter-agent communication between
Communication Agent (CA) and Processing Agent (PA) layers.

Key responsibilities:
- Manage conversation context and state
- Handle bidirectional action queues (CA ↔ PA)
- Track conversation history with timestamps
- Monitor plan progress (S1: done, S2: in_progress, etc.)
- Provide thread-safe operations for concurrent access
- Support Redis backend with in-memory fallback

Architecture:
    Communication Agent (CA) ← SharedQueueManager → Processing Agent (PA)
              ↓                        ↓                      ↓
         User Input              Redis/Memory           Background Tasks
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# ============================================================================
# Type Definitions
# ============================================================================


class ActionType(Enum):
    """Types of actions that can be queued."""

    CONVERSATION_STEP = "conversation_step"
    WAIT_FOR_PROCESSING = "wait_for_processing"
    EXECUTE_FUNCTION = "execute_function"
    UPDATE_CONTEXT = "update_context"
    GUARDRAIL_CHECK = "guardrail_check"
    PROCESS_USER_INPUT = "process_user_input"
    SEND_RESPONSE = "send_response"


class ActionDirection(Enum):
    """Direction of action flow between agent layers."""

    TO_COMMUNICATION = "to_communication"  # PA → CA
    TO_PROCESSING = "to_processing"  # CA → PA


class ActionStatus(Enum):
    """Status of queued actions."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class StepStatus(Enum):
    """Status of conversation plan steps."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class QueueAction:
    """Represents an action in the queue with directional flow."""

    id: str
    type: ActionType
    direction: ActionDirection
    status: ActionStatus
    payload: Dict[str, Any]
    priority: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type.value,
            "direction": self.direction.value,
            "status": self.status.value,
            "payload": self.payload,
            "priority": self.priority,
            "timestamp": self.timestamp.isoformat(),
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> QueueAction:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            type=ActionType(data["type"]),
            direction=ActionDirection(data["direction"]),
            status=ActionStatus(data["status"]),
            payload=data["payload"],
            priority=data.get("priority", 0),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            error=data.get("error"),
        )


@dataclass
class ConversationTurn:
    """Represents a single turn in conversation."""

    role: str  # "user" or "assistant"
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    node_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "role": self.role,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "node_id": self.node_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConversationTurn:
        """Create from dictionary."""
        return cls(
            role=data["role"],
            message=data["message"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            node_id=data.get("node_id"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class SharedQueueState:
    """Complete state managed by SharedQueueManager."""

    conversation_id: str
    context: Dict[str, Any] = field(default_factory=dict)
    action_queue: List[QueueAction] = field(default_factory=list)
    conversation_history: List[ConversationTurn] = field(default_factory=list)
    plan_progress: Dict[str, StepStatus] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "conversation_id": self.conversation_id,
            "context": self.context,
            "action_queue": [action.to_dict() for action in self.action_queue],
            "conversation_history": [
                turn.to_dict() for turn in self.conversation_history
            ],
            "plan_progress": {
                step_id: status.value for step_id, status in self.plan_progress.items()
            },
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SharedQueueState:
        """Create from dictionary."""
        return cls(
            conversation_id=data["conversation_id"],
            context=data.get("context", {}),
            action_queue=[
                QueueAction.from_dict(action) for action in data.get("action_queue", [])
            ],
            conversation_history=[
                ConversationTurn.from_dict(turn)
                for turn in data.get("conversation_history", [])
            ],
            plan_progress={
                step_id: StepStatus(status)
                for step_id, status in data.get("plan_progress", {}).items()
            },
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


# ============================================================================
# SharedQueueManager - Main Class
# ============================================================================


class SharedQueueManager:
    """
    Central state management for conversational agents.

    This class provides thread-safe operations for managing conversation state,
    bidirectional action queues (CA ↔ PA), and inter-agent communication.
    Supports Redis backend with automatic fallback to in-memory storage.

    Example:
        >>> queue = SharedQueueManager(conversation_id="conv_123")
        >>> await queue.initialize()
        >>>
        >>> # CA pushes action to PA
        >>> await queue.push_action(
        ...     action_type=ActionType.PROCESS_USER_INPUT,
        ...     direction=ActionDirection.TO_PROCESSING,
        ...     payload={"user_input": "Book a flight"}
        ... )
        >>>
        >>> # PA pops action
        >>> action = await queue.pop_action(direction=ActionDirection.TO_PROCESSING)
        >>>
        >>> # PA pushes result back to CA
        >>> await queue.push_action(
        ...     action_type=ActionType.SEND_RESPONSE,
        ...     direction=ActionDirection.TO_COMMUNICATION,
        ...     payload={"response": "I'll help you book a flight"}
        ... )
    """

    def __init__(
        self,
        conversation_id: str,
        redis_client: Optional[Any] = None,
        use_redis: bool = True,
    ) -> None:
        """
        Initialize SharedQueueManager.

        Args:
            conversation_id: Unique identifier for this conversation
            redis_client: Optional Redis client instance
            use_redis: Whether to use Redis backend (True) or in-memory (False)
        """
        self.conversation_id = conversation_id
        self._redis_client = redis_client
        self._use_redis = use_redis and redis_client is not None

        # In-memory state (used as cache or primary storage)
        self._state = SharedQueueState(conversation_id=conversation_id)

        # Thread-safety
        import threading

        self._lock = threading.Lock()

        logger.info(
            f"SharedQueueManager initialized for {conversation_id} "
            f"(backend: {'Redis' if self._use_redis else 'Memory'})"
        )

    # ========================================================================
    # Initialization
    # ========================================================================

    async def initialize(self) -> None:
        """
        Initialize the queue manager and load existing state if available.

        If using Redis, attempts to load existing state for this conversation_id.
        Falls back to in-memory if Redis is unavailable.
        """
        if self._use_redis:
            try:
                await self._load_from_redis()
                logger.info(f"Loaded state from Redis for {self.conversation_id}")
            except Exception as e:
                logger.warning(
                    f"Failed to load from Redis, using in-memory: {e}",
                    exc_info=True,
                )
                self._use_redis = False

    async def reset(self) -> None:
        """Reset state for new conversation."""
        with self._lock:
            self._state = SharedQueueState(conversation_id=self.conversation_id)

        if self._use_redis:
            await self._save_to_redis()

        logger.info(f"Reset state for {self.conversation_id}")

    # ========================================================================
    # Action Queue Operations
    # ========================================================================

    async def push_action(
        self,
        action_type: ActionType,
        direction: ActionDirection,
        payload: Dict[str, Any],
        priority: int = 0,
    ) -> str:
        """
        Push a new action to the queue with direction.

        Actions with higher priority values are processed first.

        Args:
            action_type: Type of action to queue
            direction: Direction of action flow (TO_COMMUNICATION or TO_PROCESSING)
            payload: Action-specific data
            priority: Priority level (higher = more urgent)

        Returns:
            Action ID for tracking
        """
        action_id = str(uuid.uuid4())

        action = QueueAction(
            id=action_id,
            type=action_type,
            direction=direction,
            status=ActionStatus.PENDING,
            payload=payload,
            priority=priority,
        )

        with self._lock:
            self._state.action_queue.append(action)
            # Sort by priority (descending)
            self._state.action_queue.sort(key=lambda a: a.priority, reverse=True)
            self._state.updated_at = datetime.now()

        if self._use_redis:
            await self._save_to_redis()

        logger.debug(
            f"Pushed action {action_id} ({action_type.value}) "
            f"{direction.value} with priority {priority}"
        )

        return action_id

    async def pop_action(
        self, direction: Optional[ActionDirection] = None
    ) -> Optional[QueueAction]:
        """
        Pop the highest priority pending action from the queue.

        Args:
            direction: Optional filter by direction
                      - TO_COMMUNICATION: Get actions for CA
                      - TO_PROCESSING: Get actions for PA
                      - None: Get any action

        Returns:
            Next action to process, or None if queue is empty
        """
        with self._lock:
            # Find first pending action (already sorted by priority)
            for action in self._state.action_queue:
                if action.status == ActionStatus.PENDING:
                    # Check direction filter
                    if direction is None or action.direction == direction:
                        # Mark as in-progress
                        action.status = ActionStatus.IN_PROGRESS
                        self._state.updated_at = datetime.now()

                        if self._use_redis:
                            # Save in background (don't block)
                            import asyncio

                            asyncio.create_task(self._save_to_redis())

                        logger.debug(
                            f"Popped action {action.id} ({action.type.value}) "
                            f"{action.direction.value}"
                        )
                        return action

        return None

    async def update_action_status(
        self,
        action_id: str,
        status: ActionStatus,
        error: Optional[str] = None,
    ) -> None:
        """
        Update the status of an action.

        Args:
            action_id: ID of the action to update
            status: New status
            error: Optional error message if status is FAILED
        """
        with self._lock:
            for action in self._state.action_queue:
                if action.id == action_id:
                    action.status = status
                    if error:
                        action.error = error
                    self._state.updated_at = datetime.now()

                    if self._use_redis:
                        import asyncio

                        asyncio.create_task(self._save_to_redis())

                    logger.debug(f"Updated action {action_id} to {status.value}")
                    return

        logger.warning(f"Action {action_id} not found in queue")

    async def get_pending_actions(
        self, direction: Optional[ActionDirection] = None
    ) -> List[QueueAction]:
        """
        Get all pending actions sorted by priority.

        Args:
            direction: Optional filter by direction

        Returns:
            List of pending actions
        """
        with self._lock:
            actions = [
                action
                for action in self._state.action_queue
                if action.status == ActionStatus.PENDING
            ]

            if direction is not None:
                actions = [a for a in actions if a.direction == direction]

            return actions

    async def clear_completed_actions(self) -> int:
        """
        Remove completed/failed actions from queue.

        Returns:
            Number of actions removed
        """
        with self._lock:
            original_count = len(self._state.action_queue)
            self._state.action_queue = [
                action
                for action in self._state.action_queue
                if action.status in (ActionStatus.PENDING, ActionStatus.IN_PROGRESS)
            ]
            removed_count = original_count - len(self._state.action_queue)
            self._state.updated_at = datetime.now()

        if removed_count > 0 and self._use_redis:
            await self._save_to_redis()

        logger.debug(f"Cleared {removed_count} completed actions")
        return removed_count

    # ========================================================================
    # Context Management
    # ========================================================================

    async def get_context(self) -> Dict[str, Any]:
        """Get current conversation context."""
        with self._lock:
            return self._state.context.copy()

    async def update_context(self, updates: Dict[str, Any]) -> None:
        """
        Update conversation context.

        Args:
            updates: Dictionary of context updates to merge
        """
        with self._lock:
            self._state.context.update(updates)
            self._state.updated_at = datetime.now()

        if self._use_redis:
            await self._save_to_redis()

        logger.debug(f"Updated context with keys: {list(updates.keys())}")

    async def get_context_field(self, key: str) -> Optional[Any]:
        """Get a specific field from context."""
        with self._lock:
            return self._state.context.get(key)

    # ========================================================================
    # Conversation History
    # ========================================================================

    async def add_turn(
        self,
        role: str,
        message: str,
        node_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a conversation turn to history.

        Args:
            role: "user" or "assistant"
            message: The message content
            node_id: Optional node ID associated with this turn
            metadata: Optional metadata for this turn
        """
        turn = ConversationTurn(
            role=role,
            message=message,
            node_id=node_id,
            metadata=metadata or {},
        )

        with self._lock:
            self._state.conversation_history.append(turn)
            self._state.updated_at = datetime.now()

        if self._use_redis:
            await self._save_to_redis()

        logger.debug(f"Added {role} turn to history (node: {node_id})")

    async def get_history(
        self, last_n: Optional[int] = None
    ) -> List[ConversationTurn]:
        """
        Get conversation history.

        Args:
            last_n: If specified, return only last N turns

        Returns:
            List of conversation turns
        """
        with self._lock:
            history = self._state.conversation_history.copy()

        if last_n is not None:
            return history[-last_n:]
        return history

    async def get_turn_count(self) -> int:
        """Get total number of conversation turns."""
        with self._lock:
            return len(self._state.conversation_history)

    # ========================================================================
    # Plan Progress Tracking
    # ========================================================================

    async def update_plan_progress(self, step_id: str, status: StepStatus) -> None:
        """
        Update the progress of a conversation plan step.

        Args:
            step_id: Step identifier (e.g., "S1", "S2")
            status: New status for the step
        """
        with self._lock:
            self._state.plan_progress[step_id] = status
            self._state.updated_at = datetime.now()

        if self._use_redis:
            await self._save_to_redis()

        logger.debug(f"Updated plan progress: {step_id} → {status.value}")

    async def get_plan_progress(self) -> Dict[str, StepStatus]:
        """Get current plan progress."""
        with self._lock:
            return self._state.plan_progress.copy()

    async def get_step_status(self, step_id: str) -> Optional[StepStatus]:
        """Get status of a specific step."""
        with self._lock:
            return self._state.plan_progress.get(step_id)

    async def get_completed_steps(self) -> List[str]:
        """Get list of completed step IDs."""
        with self._lock:
            return [
                step_id
                for step_id, status in self._state.plan_progress.items()
                if status == StepStatus.COMPLETED
            ]

    async def get_pending_steps(self) -> List[str]:
        """Get list of pending step IDs."""
        with self._lock:
            return [
                step_id
                for step_id, status in self._state.plan_progress.items()
                if status == StepStatus.PENDING
            ]

    # ========================================================================
    # State Inspection
    # ========================================================================

    async def get_full_state(self) -> SharedQueueState:
        """Get complete state snapshot."""
        with self._lock:
            # Create a deep copy
            return SharedQueueState(
                conversation_id=self._state.conversation_id,
                context=self._state.context.copy(),
                action_queue=self._state.action_queue.copy(),
                conversation_history=self._state.conversation_history.copy(),
                plan_progress=self._state.plan_progress.copy(),
                created_at=self._state.created_at,
                updated_at=self._state.updated_at,
            )

    async def get_summary(self) -> Dict[str, Any]:
        """Get a summary of current state."""
        with self._lock:
            pending_to_ca = len(
                [
                    a
                    for a in self._state.action_queue
                    if a.status == ActionStatus.PENDING
                    and a.direction == ActionDirection.TO_COMMUNICATION
                ]
            )
            pending_to_pa = len(
                [
                    a
                    for a in self._state.action_queue
                    if a.status == ActionStatus.PENDING
                    and a.direction == ActionDirection.TO_PROCESSING
                ]
            )

            return {
                "conversation_id": self.conversation_id,
                "turn_count": len(self._state.conversation_history),
                "pending_actions_to_ca": pending_to_ca,
                "pending_actions_to_pa": pending_to_pa,
                "completed_steps": len(
                    [
                        s
                        for s in self._state.plan_progress.values()
                        if s == StepStatus.COMPLETED
                    ]
                ),
                "total_steps": len(self._state.plan_progress),
                "created_at": self._state.created_at.isoformat(),
                "updated_at": self._state.updated_at.isoformat(),
            }

    # ========================================================================
    # Redis Operations (Private)
    # ========================================================================

    async def _save_to_redis(self) -> None:
        """Save current state to Redis."""
        if not self._use_redis or not self._redis_client:
            return

        try:
            import json

            key = f"shared_queue:{self.conversation_id}"
            data = self._state.to_dict()
            serialized = json.dumps(data)

            # Use async Redis if available
            if hasattr(self._redis_client, "set"):
                await self._redis_client.set(key, serialized)
            else:
                # Fallback to sync
                self._redis_client.set(key, serialized)

        except Exception as e:
            logger.error(f"Failed to save to Redis: {e}", exc_info=True)
            # Don't fail the operation, just log

    async def _load_from_redis(self) -> None:
        """Load state from Redis."""
        if not self._use_redis or not self._redis_client:
            return

        import json

        key = f"shared_queue:{self.conversation_id}"

        # Use async Redis if available
        if hasattr(self._redis_client, "get"):
            data_str = await self._redis_client.get(key)
        else:
            # Fallback to sync
            data_str = self._redis_client.get(key)

        if data_str:
            data = json.loads(data_str)
            self._state = SharedQueueState.from_dict(data)


# ============================================================================
# Factory Functions
# ============================================================================


def create_shared_queue_manager(
    conversation_id: str,
    redis_url: Optional[str] = None,
    use_redis: bool = True,
) -> SharedQueueManager:
    """
    Factory function to create SharedQueueManager with optional Redis.

    Args:
        conversation_id: Unique conversation identifier
        redis_url: Optional Redis connection URL
        use_redis: Whether to attempt Redis connection

    Returns:
        Configured SharedQueueManager instance
    """
    redis_client = None

    if use_redis and redis_url:
        try:
            import redis.asyncio as redis

            redis_client = redis.from_url(redis_url)
            logger.info(f"Connected to Redis at {redis_url}")
        except Exception as e:
            logger.warning(
                f"Failed to connect to Redis, using in-memory: {e}",
                exc_info=True,
            )

    return SharedQueueManager(
        conversation_id=conversation_id,
        redis_client=redis_client,
        use_redis=use_redis,
    )
