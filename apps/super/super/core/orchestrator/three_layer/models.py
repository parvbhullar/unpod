"""Data models for three-layer orchestration."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


class ActionStatus(Enum):
    """Status of an action in the queue."""

    PENDING = "pending"
    PROCESSING = "processing"
    WAITING = "waiting"
    DONE = "done"
    CANCELLED = "cancelled"


class ExecutionMode(Enum):
    """Execution mode for actions."""

    SYNC = "sync"
    ASYNC = "async"


class PlanStep(TypedDict):
    """A step in a multi-step plan."""

    step_id: str
    name: str
    status: str  # pending, running, done, skipped
    input: Optional[Dict[str, Any]]
    result: Optional[Dict[str, Any]]


class PlanState(TypedDict):
    """State of a multi-step plan."""

    plan_id: str
    steps: List[PlanStep]
    current_step: int
    is_complete: bool


class ActionState(TypedDict):
    """State of an action in the shared context."""

    action_id: str
    thread_id: str
    input: str
    status: ActionStatus
    mode: Optional[ExecutionMode]
    engagement: Optional[str]
    plan: Optional[PlanState]
    waiting_for: Optional[str]
    result: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str
    supersedes: Optional[str]


def create_action_state(
    action_id: str,
    thread_id: str,
    input_text: str,
    mode: Optional[ExecutionMode] = None,
    supersedes: Optional[str] = None,
) -> ActionState:
    """Create a new ActionState with defaults."""
    now = datetime.utcnow().isoformat()
    return ActionState(
        action_id=action_id,
        thread_id=thread_id,
        input=input_text,
        status=ActionStatus.PENDING,
        mode=mode,
        engagement=None,
        plan=None,
        waiting_for=None,
        result=None,
        created_at=now,
        updated_at=now,
        supersedes=supersedes,
    )
