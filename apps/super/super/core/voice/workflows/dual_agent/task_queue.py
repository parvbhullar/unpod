"""
Task Queue - Priority-based async task management between Communication and Processing agents

This module provides the Task Queue that enables async communication between:
- Communication Agent (pushes tasks, checks status)
- Processing Agent (polls tasks, executes, updates status)
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import uuid


class TaskPriority(Enum):
    """Task priority levels"""
    HIGH = "HIGH"      # User-facing queries (immediate response needed)
    MEDIUM = "MEDIUM"  # Background processing
    LOW = "LOW"        # Pre-fetching, caching


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "PENDING"          # Waiting for Processing Agent
    IN_PROGRESS = "IN_PROGRESS"  # Currently executing
    COMPLETED = "COMPLETED"       # Successfully completed
    FAILED = "FAILED"             # Execution failed


class TaskType(Enum):
    """Types of tasks that can be executed"""
    KB_SEARCH = "kb_search"                # Knowledge base semantic search
    DB_QUERY = "db_query"                  # Database query
    ELIGIBILITY_CHECK = "eligibility_check" # Business logic check
    API_CALL = "api_call"                  # External API call
    COMPUTE = "compute"                     # Heavy computation


@dataclass
class Task:
    """
    Individual task in the queue.

    Attributes:
        task_id: Unique identifier
        priority: Task priority (HIGH, MEDIUM, LOW)
        status: Current status (PENDING, IN_PROGRESS, COMPLETED, FAILED)
        task_type: Type of task to execute
        query: User's question or search query
        context: Relevant context for task execution
        filler_message: Message for Communication Agent to speak while waiting
        timeout_threshold: Max execution time in milliseconds
        result: Task execution result (when COMPLETED)
        error: Error message (when FAILED)
    """
    task_id: str
    priority: TaskPriority
    status: TaskStatus
    task_type: TaskType

    # Task definition
    query: str
    context: Dict[str, Any] = field(default_factory=dict)

    # Communication Agent support
    filler_message: str = "I'm looking into that for you..."
    timeout_threshold: int = 10000  # 10 seconds

    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Results
    result: Optional[Any] = None
    error: Optional[str] = None

    def is_timed_out(self) -> bool:
        """Check if task has exceeded timeout threshold"""
        if self.started_at is None:
            return False

        elapsed = (datetime.now() - self.started_at).total_seconds() * 1000
        return elapsed > self.timeout_threshold


class TaskQueue:
    """
    Priority-based async task queue.

    Enables Communication Agent and Processing Agent to work independently:
    - Communication Agent: Pushes tasks, checks status, retrieves results
    - Processing Agent: Polls for pending tasks, executes, updates status

    Thread-safe via asyncio locks.
    """

    def __init__(self):
        self._tasks: Dict[str, Task] = {}  # task_id -> Task
        self._pending: List[str] = []      # Pending task IDs (priority-sorted)
        self._lock = asyncio.Lock()

    async def push_task(
        self,
        task_type: str,
        query: str,
        priority: str = "MEDIUM",
        context: Dict[str, Any] = None,
        filler_message: str = None,
        timeout_threshold: int = 10000
    ) -> str:
        """
        Push new task to queue.

        Args:
            task_type: Type of task (kb_search, db_query, etc.)
            query: User's question or search query
            priority: Task priority (HIGH, MEDIUM, LOW)
            context: Relevant context for task execution
            filler_message: Message to speak while waiting
            timeout_threshold: Max execution time in ms

        Returns:
            task_id: Unique task identifier
        """
        async with self._lock:
            task_id = str(uuid.uuid4())

            task = Task(
                task_id=task_id,
                priority=TaskPriority[priority],
                status=TaskStatus.PENDING,
                task_type=TaskType[task_type.upper()],
                query=query,
                context=context or {},
                filler_message=filler_message or "I'm looking into that for you...",
                timeout_threshold=timeout_threshold
            )

            self._tasks[task_id] = task
            self._pending.append(task_id)

            # Sort by priority (HIGH first, then MEDIUM, then LOW)
            self._pending.sort(
                key=lambda tid: self._tasks[tid].priority.value,
                reverse=False  # HIGH comes before LOW alphabetically
            )

            return task_id

    async def get_pending_tasks(self, limit: int = 10) -> List[Task]:
        """
        Get pending tasks (for Processing Agent).

        Returns tasks in priority order (HIGH first).

        Args:
            limit: Max number of tasks to return

        Returns:
            List of pending tasks
        """
        async with self._lock:
            pending_ids = self._pending[:limit]
            return [self._tasks[tid] for tid in pending_ids if tid in self._tasks]

    async def get_task_status(self, task_id: str) -> Optional[str]:
        """
        Check task status (for Communication Agent).

        Args:
            task_id: Task identifier

        Returns:
            Status string (PENDING, IN_PROGRESS, COMPLETED, FAILED) or None
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            return task.status.value if task else None

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get full task object"""
        async with self._lock:
            return self._tasks.get(task_id)

    async def update_task_status(
        self,
        task_id: str,
        status: str,
        started_at: Optional[datetime] = None
    ):
        """
        Update task status (Processing Agent uses this).

        Args:
            task_id: Task identifier
            status: New status (IN_PROGRESS, COMPLETED, FAILED)
            started_at: Timestamp when execution started
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return

            task.status = TaskStatus[status]

            if status == "IN_PROGRESS":
                task.started_at = started_at or datetime.now()

                # Remove from pending list
                if task_id in self._pending:
                    self._pending.remove(task_id)

    async def complete_task(self, task_id: str, result: Any):
        """
        Mark task as completed with result.

        Args:
            task_id: Task identifier
            result: Task execution result
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return

            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result

            # Remove from pending if still there
            if task_id in self._pending:
                self._pending.remove(task_id)

    async def fail_task(self, task_id: str, error: str):
        """
        Mark task as failed.

        Args:
            task_id: Task identifier
            error: Error message
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return

            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error = error

            # Remove from pending
            if task_id in self._pending:
                self._pending.remove(task_id)

    async def get_task_result(self, task_id: str) -> Optional[Any]:
        """
        Retrieve completed task result (for Communication Agent).

        Args:
            task_id: Task identifier

        Returns:
            Task result or None
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task or task.status != TaskStatus.COMPLETED:
                return None

            return task.result

    async def get_timed_out_tasks(self) -> List[Task]:
        """
        Get tasks that have exceeded timeout threshold.

        Returns:
            List of timed-out tasks
        """
        async with self._lock:
            return [
                task for task in self._tasks.values()
                if task.status == TaskStatus.IN_PROGRESS and task.is_timed_out()
            ]

    async def cleanup_old_tasks(self, max_age_seconds: int = 3600):
        """
        Remove old completed/failed tasks.

        Args:
            max_age_seconds: Max age of tasks to keep (default 1 hour)
        """
        async with self._lock:
            now = datetime.now()
            to_remove = []

            for task_id, task in self._tasks.items():
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                    if task.completed_at:
                        age = (now - task.completed_at).total_seconds()
                        if age > max_age_seconds:
                            to_remove.append(task_id)

            for task_id in to_remove:
                del self._tasks[task_id]

    async def get_queue_stats(self) -> Dict[str, int]:
        """Get queue statistics"""
        async with self._lock:
            return {
                "total": len(self._tasks),
                "pending": len(self._pending),
                "in_progress": sum(1 for t in self._tasks.values() if t.status == TaskStatus.IN_PROGRESS),
                "completed": sum(1 for t in self._tasks.values() if t.status == TaskStatus.COMPLETED),
                "failed": sum(1 for t in self._tasks.values() if t.status == TaskStatus.FAILED)
            }
