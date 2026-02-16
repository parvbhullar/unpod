import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

print(sys.path[0])

from services.task_service.core.task_service import TaskService


def test_task_service():
    task_service = TaskService()
    result = task_service.process_task(task_id="task123")

    print(result)


if __name__ == "__main__":
    test_task_service()
