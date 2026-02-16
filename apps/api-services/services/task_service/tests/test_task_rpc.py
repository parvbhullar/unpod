import pytest
from unittest.mock import Mock, patch
from nameko.testing.services import worker_factory

from services.task_service.services.task_service import TaskServiceRPC
from services.task_service.schemas.task import TaskStatusEnum


@pytest.fixture
def service():
    return worker_factory(TaskServiceRPC)


def test_create_run(service):
    # Test data
    space_id = "test_space"
    user = "test_user"
    collection_ref = "test_collection"
    expected_result = {
        "run_id": "R12345678",
        "space_id": space_id,
        "user": user,
        "collection_ref": collection_ref,
    }

    # Mock the task service method
    with patch.object(service.task_service, "create_run") as mock_create:
        mock_create.return_value = expected_result
        result = service.create_run(space_id, user, collection_ref)

        mock_create.assert_called_once_with(
            space_id=space_id,
            user=user,
            collection_ref=collection_ref,
            batch_count=0,
            run_mode="Dev",
            thread_id=None,
            owner_org_id=None,
        )
        assert result == expected_result


def test_add_task(service):
    # Test data
    run_id = "R123"
    task_data = {"question": "test question"}
    assignee = "test_assignee"
    collection_ref = "test_collection"
    expected_result = {"task_id": "T12345678", "run_id": run_id, "task": task_data}

    # Mock the task service method
    with patch.object(service.task_service, "add_task") as mock_add:
        mock_add.return_value = expected_result
        result = service.add_task(run_id, task_data, assignee, collection_ref)

        mock_add.assert_called_once_with(
            run_id=run_id,
            task_data=task_data,
            assignee=assignee,
            collection_ref=collection_ref,
            thread_id=None,
        )
        assert result == expected_result


def test_update_task_status(service):
    # Test data
    task_id = "T123"
    status = TaskStatusEnum.completed
    output = {"result": "test result"}
    expected_result = {"task_id": task_id, "status": status, "output": output}

    # Mock the task service method
    with patch.object(service.task_service, "update_task_status") as mock_update:
        mock_update.return_value = expected_result
        result = service.update_task_status(task_id, status, output)

        mock_update.assert_called_once_with(
            task_id=task_id, status=status, output=output
        )
        assert result == expected_result


def test_process_task_message(service):
    # Test data
    task_id = "T123"
    message = Mock()
    message.value = {"task_id": task_id}

    # Mock the task service method
    with patch.object(service.task_service, "process_task") as mock_process:
        mock_process.return_value = True
        result = service.process_task(message)

        mock_process.assert_called_once_with(task_id)
        assert result is True


def test_get_run_status(service):
    # Test data
    run_id = "R123"
    expected_result = {
        "run": {"run_id": run_id},
        "task_stats": {"total": 3, "completed": 1, "failed": 1, "pending": 1},
    }

    # Mock the task service method
    with patch.object(service.task_service, "get_run_status") as mock_get:
        mock_get.return_value = expected_result
        result = service.get_run_status(run_id)

        mock_get.assert_called_once_with(run_id)
        assert result == expected_result


def test_add_artifact(service):
    # Test data
    file_id = "F123"
    path = "/test/path"
    space_id = "test_space"
    expected_result = {"file_id": file_id, "path": path, "space_id": space_id}

    # Mock the task service method
    with patch.object(service.task_service, "add_artifact") as mock_add:
        mock_add.return_value = expected_result
        result = service.add_artifact(file_id, path, space_id)

        mock_add.assert_called_once_with(
            file_id=file_id,
            path=path,
            space_id=space_id,
            thread_id=None,
            run_id=None,
            task_id=None,
        )
        assert result == expected_result
