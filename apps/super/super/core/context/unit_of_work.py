from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any, List, Union
import enum
import uuid


class Status(str, enum.Enum):
    """Common status enum for both Task and Message"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    HOLD = "hold"

    def __str__(self):
        return self.value


class UOW(BaseModel):
    """Base Unit of Work model containing common properties."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    status: Status = Status.PENDING
    # metadata: dict = Field(default_factory=dict)


class TaskType(str, enum.Enum):
    """Types of tasks that can be performed"""

    ANALYSIS = "analysis"
    PLAN = "plan"
    EXECUTE = "execute"
    DEFAULT = "default"

    def __str__(self):
        return self.value


class ExecutionType(str, enum.Enum):
    """Types of tasks that can be performed"""

    SEARCH = "search"
    WRITE = "write"
    CREATE = "create"

    def __str__(self):
        return self.value


class Task(UOW):
    """Task model with essential fields and owner tracking"""

    objective: str
    ready_criteria: List[str]
    type: TaskType = TaskType.DEFAULT
    priority: int = 1
    parent_id: Optional[str] = None
    tasks: List["Task"] = Field(default_factory=list)
    owner_type: str = Field(default="agent")  # "agent" or "user"
    owner_id: Optional[str] = None
    owner_role: Optional[str] = None
    status_history: List[dict] = Field(default_factory=list)

    @classmethod
    def create(
        cls,
        objective: str,
        task_type: TaskType = TaskType.DEFAULT,
        priority: int = 1,
        ready_criteria: List[str] = None,
    ):
        """Factory method to create a new task"""
        return cls(
            objective=objective,
            type=task_type,
            priority=priority,
            ready_criteria=ready_criteria or ["Task created"],
        )

    def add_subtask(self, subtask: "Task"):
        """Add a subtask to this task"""
        subtask.parent_id = self.id
        self.tasks.append(subtask)

    def add_plan(self, tasks: List[Any]):
        """Add tasks from a plan to this task"""
        for task_item in tasks:
            # Handle both dict and TaskSchema objects
            if isinstance(task_item, dict):
                task_data = task_item
            else:
                # Assuming TaskSchema object with objective attribute
                task_data = {
                    "objective": task_item.objective,
                    "type": TaskType.DEFAULT,
                    "priority": 1,
                    "ready_criteria": ["Task created from schema"],
                }

            subtask = Task(
                objective=task_data.get("objective"),
                type=TaskType(task_data.get("type", TaskType.DEFAULT)),
                priority=task_data.get("priority", 1),
                ready_criteria=task_data.get("ready_criteria", ["Task created"]),
            )
            self.add_subtask(subtask)

    async def assign_owner(
        self,
        owner_id: str,
        owner_type: str = "agent",
        owner_role: Optional[str] = None,
        callback: Optional["TaskCallback"] = None,
    ):
        """Assign an owner (agent or user) to this task"""
        old_owner = {
            "type": self.owner_type,
            "id": self.owner_id,
            "role": self.owner_role,
        }
        self.owner_id = owner_id
        self.owner_type = owner_type
        self.owner_role = owner_role
        self._record_status_change(f"Assigned to {owner_type} {owner_id}")

        # Send callback notification if callback is provided
        if callback:
            await callback.on_task_owner_change(
                self,
                old_owner,
                {"type": owner_type, "id": owner_id, "role": owner_role},
            )

    async def update_status(
        self,
        new_status: Status,
        reason: str = None,
        callback: Optional["TaskCallback"] = None,
    ):
        """Update task status with validation and history tracking"""
        # Validate status transition
        valid_transitions = {
            Status.PENDING: [Status.IN_PROGRESS, Status.HOLD],
            Status.IN_PROGRESS: [Status.COMPLETED, Status.FAILED, Status.HOLD],
            Status.HOLD: [Status.IN_PROGRESS, Status.FAILED],
            Status.COMPLETED: [],  # Terminal state
            Status.FAILED: [Status.PENDING],  # Can retry failed tasks
        }

        if (
            new_status not in valid_transitions.get(self.status, [])
            and new_status != self.status
        ):
            raise ValueError(
                f"Invalid status transition from {self.status} to {new_status}"
            )

        old_status = self.status
        self.status = new_status
        self._record_status_change(
            reason or f"Status changed from {old_status} to {new_status}"
        )

        # Send callback notification if callback is provided
        if callback:
            await callback.on_task_status_change(self, old_status, new_status, reason)
            if new_status == Status.COMPLETED:
                await callback.on_task_completed(self)

    def _record_status_change(self, reason: str):
        """Record status change in history"""
        self.status_history.append(
            {
                "timestamp": datetime.now(),
                "status": self.status,
                "reason": reason,
                "owner_id": self.owner_id,
                "owner_type": self.owner_type,
                "owner_role": self.owner_role,
            }
        )


Task.update_forward_refs()
