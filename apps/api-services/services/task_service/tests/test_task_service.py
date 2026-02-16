import pytest
from unittest.mock import Mock, patch
from nameko.testing.services import worker_factory
from services.task_service.core.task_service import TaskService
from services.task_service.models.task import RunModel, TaskModel, ArtifactModel
from services.task_service.schemas.task import TaskStatusEnum


@pytest.fixture
def service():
    return worker_factory(TaskService)


def test_create_run(service):
    # Test data
    space_id = "test_space"
    user = "test_user"
    collection_ref = "test_collection"

    # Mock the create method
    with patch.object(RunModel, "create") as mock_create:
        mock_run = Mock()
        mock_run.dict.return_value = {
            "run_id": "R12345678",
            "space_id": space_id,
            "user": user,
            "collection_ref": collection_ref,
            "status": TaskStatusEnum.pending,
            "run_mode": "Dev",
        }
        mock_create.return_value = mock_run

        result = service.create_run(space_id, user, collection_ref)

        assert result["space_id"] == space_id
        assert result["user"] == user
        assert result["collection_ref"] == collection_ref
        assert result["status"] == TaskStatusEnum.pending
        assert result["run_mode"] == "Dev"


def test_add_task(service):
    # Test data
    run_id = "R123"
    task_data = {"question": "test question"}
    assignee = "test_assignee"
    collection_ref = "test_collection"

    # Mock the create method
    with patch.object(TaskModel, "create") as mock_create:
        mock_task = Mock()
        mock_task.dict.return_value = {
            "task_id": "T12345678",
            "run_id": run_id,
            "task": task_data,
            "assignee": assignee,
            "collection_ref": collection_ref,
            "status": TaskStatusEnum.pending,
        }
        mock_create.return_value = mock_task

        result = service.add_task(run_id, task_data, assignee, collection_ref)

        assert result["run_id"] == run_id
        assert result["task"] == task_data
        assert result["assignee"] == assignee
        assert result["collection_ref"] == collection_ref
        assert result["status"] == TaskStatusEnum.pending


def test_update_task_status(service):
    # Test data
    task_id = "T123"
    status = TaskStatusEnum.completed
    output = {"result": "test result"}

    # Mock find_one and update_one methods
    with patch.object(TaskModel, "find_one") as mock_find_one, patch.object(
        TaskModel, "update_one"
    ) as mock_update_one:
        mock_task = Mock()
        mock_task.dict.return_value = {
            "task_id": task_id,
            "status": status,
            "output": output,
        }
        mock_find_one.return_value = mock_task

        result = service.update_task_status(task_id, status, output)

        mock_update_one.assert_called_once_with(
            {"task_id": task_id}, {"$set": {"status": status, "output": output}}
        )
        assert result["task_id"] == task_id
        assert result["status"] == status
        assert result["output"] == output


def test_get_run_status(service):
    # Test data
    run_id = "R123"

    # Mock find_one and find methods
    with patch.object(RunModel, "find_one") as mock_find_one, patch.object(
        TaskModel, "find"
    ) as mock_find:
        mock_run = Mock()
        mock_run.dict.return_value = {"run_id": run_id}
        mock_find_one.return_value = mock_run

        mock_tasks = [
            Mock(status=TaskStatusEnum.completed),
            Mock(status=TaskStatusEnum.failed),
            Mock(status=TaskStatusEnum.pending),
        ]
        mock_find.return_value = mock_tasks

        result = service.get_run_status(run_id)

        assert result["run"]["run_id"] == run_id
        assert result["task_stats"]["total"] == 3
        assert result["task_stats"]["completed"] == 1
        assert result["task_stats"]["failed"] == 1
        assert result["task_stats"]["pending"] == 1


def test_add_artifact(service):
    # Test data
    file_id = "F123"
    path = "/test/path"
    space_id = "test_space"

    # Mock the create method
    with patch.object(ArtifactModel, "create") as mock_create:
        mock_artifact = Mock()
        mock_artifact.dict.return_value = {
            "file_id": file_id,
            "path": path,
            "space_id": space_id,
        }
        mock_create.return_value = mock_artifact

        result = service.add_artifact(file_id, path, space_id)

        assert result["file_id"] == file_id
        assert result["path"] == path
        assert result["space_id"] == space_id
