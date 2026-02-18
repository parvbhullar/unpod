import json

from prefect import task, flow
from prefect.runtime import flow_run
from super.app.call_profile import update_profile_by_task_id
from super_services.db.services.models.task import TaskModel, RunModel
from dataclasses import dataclass, asdict
from super.app.providers.base import CallResult
from super.core.voice.schema import UserState
from super.core.voice.common.services import save_execution_log
from super_services.db.services.schemas.task import TaskStatusEnum

from super.core.voice.schema import UserState


@dataclass
class FlowJob:
    task_id: str
    call_result: CallResult
    user_state: UserState


@task(name="post-call-workflow")
async def post_call_workflow(
    task: TaskModel, call_result: CallResult, user_state: UserState
):
    from super.app.call_execution import execute_post_call_workflow
    from super_services.voice.models.config import ModelConfig

    task_data = {
        "task_id": task.task_id,
        "instructions": task.task.get("objective"),
        "input": task.input,
    }

    try:
        post_call_result = await execute_post_call_workflow(
            task.assignee, ModelConfig(), call_result, task_data, True, user_state
        )

        if post_call_result:
            return post_call_result
        else:
            return {}
    except Exception as e:
        print(f"unable t run post call workflow {str(e)}")
        return {}


@task(name="build-task-output")
async def create_task_output(
    call_result: CallResult, post_call_result, user_state: UserState = None
):
    new_output = {}
    try:
        cost = (
            float(call_result.data.get("cost", 0.0))
            + (float(call_result.data.get("cost", 0.0)) * 5) / 100
        )

        number = call_result.contact_number

        if isinstance(number, str) and number.startswith("0"):
            number=number[1:]

        new_output = {
            "call_id": call_result.call_id,
            "customer": call_result.customer,
            "contact_number": number,
            "call_end_reason": call_result.call_end_reason,
            "recording_url": call_result.recording_url,
            "transcript": call_result.transcript,
            "start_time": call_result.call_start,
            "end_time": call_result.call_end,
            "assistant_number": call_result.assistant_number,
            "call_summary": call_result.call_summary,
            "duration": (call_result.duration if call_result.duration else 0),
            "cost": cost,
            "post_call_data": post_call_result,
            "metadata": {
                "cost": cost,
                "type": call_result.data.get("type", "outbound"),
                "usage": call_result.data.get("usage", {}),
            },
        }

        if user_state:
            new_output["call_type"] = (
                user_state.extra_data.get("call_type") if user_state.extra_data else ""
            )

        if call_result.status == "failed":
            new_output = {}

        if call_result.error:
            new_output["error"] = call_result.error
        if call_result.notes:
            new_output["notes"] = call_result.notes
        if call_result.call_summary:
            new_output["call_summary"] = call_result.call_summary
        if call_result.call_status:
            new_output["call_status"] = call_result.call_status
        if call_result.status_update:
            new_output["status_update"] = call_result.status_update

    except Exception as e:
        raise Exception(f"Error executing call response: {str(e)}")
        response = {}
        response["status"] = "failed"
        response["data"] = {
            "call_id": call_result.call_id,
            "customer": call_result.customer,
            "error": f"Failed to format response: {str(e)}",
        }
        return response

    return new_output


@task(name="update-task")
async def update_task(
    task: TaskModel, call_result, doc_id=None, doc_ref=None, name=None
):
    if name:
        call_result["customer"] = name

    updated_data = {"status": TaskStatusEnum.completed, "output": call_result}

    run_data = {"status": TaskStatusEnum.completed}
    if doc_ref and doc_id:
        updated_data["ref_id"] = doc_id
        updated_data["collection_ref"] = doc_ref
        run_data["collection_ref"] = doc_ref

    TaskModel.update_one({"task_id": task.task_id}, updated_data)
    RunModel.update_one({"run_id": task.run_id}, run_data)

    await save_execution_log(
        task_id=task.task_id,
        step="Task updation creation",
        status="success",
        output="update successful",
    )

    return


@task(name="create_call_log")
def create_call_log(call_result, task_output, task_id):
    print("creating call log")
    response = {"status": call_result.call_status, "data": task_output}

    if task_output.get("call_status") and isinstance(task_output, dict):
        response["status"] = task_output.get("call_status")

    from super_services.orchestration.task.task_service import TaskService

    task = TaskModel.get(task_id=task_id)

    service = TaskService()
    service.insert_call_log(response=response, data=task_output, task=task)


@task(name="create-doc")
async def get_doc_id(user_state, post_call_result, task_id):
    from super.core.voice.common.services import (
        create_collection_doc,
        get_doc_id_from_number,
    )

    doc_id, name = await get_doc_id_from_number(
        user_state.contact_number, user_state.token
    )

    if doc_id:
        return doc_id, name

    try:
        if isinstance(post_call_result.get("structured_data"), str):
            name = json.loads(
                post_call_result.get(
                    "structured_data",
                )
            ).get("name")
        else:
            name = post_call_result.get("structured_data", {}).get("name", "")
    except Exception as e:
        name = None

    if isinstance(post_call_result.get("classification"), str):
        labels = json.loads(post_call_result.get("classification", {})).get(
            "labels", []
        )
    else:
        labels = post_call_result.get("classification", {}).get("labels", [])

    number = (
        user_state.contact_number[1]
        if user_state.contact_number and user_state.contact_number.startswith("0")
        else user_state.contact_number
    )

    payload = {
        "name": name if name else user_state.user_name,
        "contact_number": number,
        "labels": labels,
    }

    doc_id = await create_collection_doc(user_state, payload)

    await save_execution_log(
        task_id=task_id,
        step="doc creation",
        status="success",
        output=doc_id,
    )

    return doc_id, user_state.user_name


def generate_post_flow_name():
    parameters = flow_run.parameters
    job = parameters["job"]
    job = asdict(job)
    task_id = job["task_id"]
    return f"post-call-flow-{task_id}"


@flow(
    name="Post Call Flow",
    description="Post Call Flow",
    flow_run_name=generate_post_flow_name,
    log_prints=True,
)
async def post_call_flow(job: FlowJob):
    if not job.task_id:
        raise ValueError("Task not found, No task_id provided")
    current_task = TaskModel.get(task_id=job.task_id)
    post_call_result = await post_call_workflow(
        current_task, job.call_result, job.user_state
    )

    if post_call_result.get("is_redial"):
        print("call in instant redial waiting for redial to update task")
        return

    task_output = await create_task_output(
        call_result=job.call_result,
        post_call_result=post_call_result,
        user_state=job.user_state,
    )

    create_call_log(job.call_result, task_output, job.task_id)

    print(f"\n\n {task_output} \n\n")

    if not current_task.ref_id:
        doc_id, name = await get_doc_id(job.user_state, post_call_result, job.task_id)

        doc_ref = f"collection_data_{job.user_state.token}"

        await update_task(current_task, task_output, doc_id, doc_ref, name)
        await update_profile_by_task_id(job.task_id)
    else:
        await update_task(current_task, task_output)

if __name__ == "__main__":
    from super_services.voice.models.config import ModelConfig
    job=FlowJob(
        task_id="T0c81bc0d072311f1878d43cd8a99e069",
        call_result=CallResult(
            status="notConnected",
            data={}
        ),
        user_state=UserState(
        model_config=ModelConfig().get_config('digital-recruitment-agent-1jq7qhesciwb')
        ),
    )
    import asyncio
    asyncio.run(post_call_flow(job))