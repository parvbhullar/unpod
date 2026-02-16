from typing import Optional
from datetime import datetime

from super.core.callback.base import BaseCallback
from super.core.context.schema import Message
from super.core.context.unit_of_work import Status, Task


class TaskCallback(BaseCallback):
    """Callback handler for task-related events"""

    async def send(self, message, **kwargs):
        """Send a message."""
        print(f"Task callback sending: {message}")

    async def receive(self, message, **kwargs):
        """Receive a message."""
        print(f"Task callback received: {message}")

    async def on_task_status_change(
        self,
        task: Task,
        old_status: Status,
        new_status: Status,
        reason: Optional[str] = None,
    ):
        """Handle task status change events"""
        message = (
            f"Task '{task.objective}' status changed from {old_status} to {new_status}"
            f"\nOwner: {task.owner_type} ({task.owner_id})"
            + (f"\nRole: {task.owner_role}" if task.owner_role else "")
            + (f"\nReason: {reason}" if reason else "")
        )
        await self.send(Message.add_notification(message))

    async def on_task_owner_change(self, task: Task, old_owner: dict, new_owner: dict):
        """Handle task owner change events"""
        message = (
            f"Task '{task.objective}' ownership changed:\n"
            f"From: {old_owner.get('type', 'None')} ({old_owner.get('id', 'None')})\n"
            f"To: {new_owner.get('type', 'None')} ({new_owner.get('id', 'None')})"
        )
        await self.send(Message.add_notification(message))

    async def on_task_created(self, task: Task):
        """Handle task creation events"""
        message = (
            f"New task created: '{task.objective}'\n"
            f"Priority: {task.priority}\n"
            f"Type: {task.type}"
        )
        await self.send(Message.add_notification(message))

    async def on_task_completed(self, task: Task):
        """Handle task completion events"""
        duration = datetime.now() - task.timestamp
        message = (
            f"Task completed: '{task.objective}'\n"
            f"Duration: {duration}\n"
            f"Owner: {task.owner_type} ({task.owner_id})"
        )
        await self.send(Message.add_notification(message))
