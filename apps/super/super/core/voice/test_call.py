# from .call_execution import (
#     execute_call,
#     # , start_vapi_call
# )

# from super.apps.calls_orc.livkit.voice_agents.test_agent_config import ModelConfig
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
sys.path.pop(1)
import asyncio
from super.app.call_execution import execute_call
from super_services.voice.models.config import ModelConfig
from super_services.voice.common.threads import (
    create_thread_post,
    update_thread,
    get_user_id,
)

data = {
    "name": "Arshpreet",
    "time": "tt",
    "about": "tt",
    "email": "arsh@gmail.com",
    "number": "9738301026",
    "address": "mohali",
    "context": "tt",
    "multi_select": "tt",
    "contact_number": "8847348129",
    "created": "2025-08-14T07:18:31.968000",
    "date_and_time": "tt",
    "title": "8847348129",
    "description": "Arshpreet",
    "document_id": "689d8dc77ba71026cbd36ce8",
    "token": "F1O3QJM1Y7Q1AVVUYNV4VPRB",
    "quality": "good",
    "vapi_agent_id": "12364cc",
}


async def test_call_with_task(task_id):
    from super_services.db.services.models.task import TaskModel
    from super_services.db.services.schemas.task import TaskStatusEnum
    from super_services.orchestration.webhook.webhook_handler import WebhookHandler
    from super_services.orchestration.task.task_service import TaskService
    from super_services.voice.consumers.voice_task_consumer import (
        sanitize_data_for_mongodb,
    )
    from super_services.voice.models.config import MessageCallBack

    task = TaskModel.get(task_id=task_id)
    task_id = task.task_id

    print(f"task found {task.assignee}")

    data = task.input

    data["thread_id"] = (
        create_thread_post(task_id)
        if not data.get("thread_id")
        else data.get("thread_id")
    )
    data["user_id"] = (
        get_user_id(task_id) if not data.get("user_id") else data.get("user_id")
    )

    response = await execute_call(
        data=data,
        task_id=task.task_id,
        agent_id=task.assignee,
        instructions="",
        model_config=ModelConfig(),
        callback=MessageCallBack(),
    )

    webhook_handler = WebhookHandler()
    task_service = TaskService()

    print(response, "kafka_response")

    return response

    if response and response.get("status") == "completed":
        print(f"Call task {task_id} completed successfully", "kafka_task_success")
        # Update task status to completed
        try:
            # Sanitize data before database update to handle datetime/timedelta objects
            sanitized_data = sanitize_data_for_mongodb(response.get("data", {}))
            updated_task = task_service.update_task_status(
                task_id, TaskStatusEnum.completed, sanitized_data
            )
            await webhook_handler.execute(task_id=task_id)
            update_thread(task_id, sanitized_data)

        except Exception as db_ex:
            print(
                f"Database update failed for completed task {task_id}, sanitizing further: {str(db_ex)}",
                "mongo_db_error",
            )
            # Fallback: convert problematic data to strings
            fallback_data = {
                "error": "Data sanitization required",
                "original_error": str(db_ex),
                "data_summary": str(response.get("data", {}))[
                    :1000
                ],  # Truncate to avoid huge logs
            }
            updated_task = task_service.update_task_status(
                task_id, TaskStatusEnum.completed, fallback_data
            )
            await webhook_handler.execute(task_id=task_id)

    elif response.get("status") == "in_progress":
        print(f"Call task {task_id} in progress", "kafka_task_in_progress")
        # sanitized_data = sanitize_data_for_mongodb(response.get("data", {}))
        # updated_task = task_service.update_task_status(
        #     task_id, TaskStatusEnum.in_progress, sanitized_data
        # )

    elif response.get("status") == "failed":
        print(f"Call task {task_id} failed", "kafka_task_failed")
        # sanitized_data = sanitize_data_for_mongodb(response.get("data", {}))
        # updated_task = task_service.update_task_status(
        #     task_id, TaskStatusEnum.failed, sanitized_data
        # )
        # await webhook_handler.execute(task_id=task_id)


async def test(data):
    res = await execute_call(
        data=data,
        task_id="123",
        agent_id="pipecat-test-agent",
        # agent_id = "testing-good-qua.-xkc0gsvr7ns7",
        instructions="",
        model_config=ModelConfig(),
        callback=None,
    )


async def run_multi():
    res = await asyncio.gather(
        test_call_with_task("T7d2da1ebe9fc11ef8e2a91681c5ad3ab"),
        test_call_with_task("T607f0bfd01c611f186e314b5cd48690a"),
        test_call_with_task("Tefe4015f78de11f082ac156368e7acc4"),
        test_call_with_task("T83ab60e7f8df11f0878d43cd8a99e069"),
    )

    for i in res:
        print(f"{'='*50} \n\n {i} \n\n {'='*50}")
    return res


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run tasks in single or multi mode.")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--single", action="store_true", help="Run in single mode")
    group.add_argument("--multi", action="store_true", help="Run in multi mode")

    args = parser.parse_args()

    if args.multi:
        asyncio.run(run_multi())
    else:
        asyncio.run(test_call_with_task("Tefe4015f78de11f082ac156368e7acc4"))
        # asyncio.run(test_call_with_task("T67b64245074511f1878d43cd8a99e069"))
