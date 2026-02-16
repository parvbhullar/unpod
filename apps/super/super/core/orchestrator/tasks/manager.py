"""Stub: TaskManager for orchestrator."""

from typing import List, Any


class TaskManager:
    """Simple task manager stub."""

    def __init__(self):
        self._tasks = []

    def add_task(self, task: Any):
        self._tasks.append(task)

    def get_tasks_by_status(self, status: Any) -> List:
        return [t for t in self._tasks if getattr(t, "status", None) == status]

    def get_ready_tasks(self) -> List:
        return [t for t in self._tasks if not getattr(t, "dependencies", [])]

    def update_status(self, task_id: str, status: Any):
        for task in self._tasks:
            if getattr(task, "id", None) == task_id:
                task.status = status
                break
