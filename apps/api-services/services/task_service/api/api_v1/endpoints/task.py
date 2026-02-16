from typing import Optional
import dateutil
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request
from services.messaging_service.schemas.response import (
    DynamicResponseModelWithPagination,
)
from services.task_service.core.task_service import TaskService
from services.task_service.models.api_models import (
    APIRequestModel,
    APIResponseModel,
    RunsListModel,
    TaskListModel,
    Task,
)
from services.task_service.services.connector import fetch_contact_data
from services.task_service.services.prefect import trigger_deployment

router = APIRouter()
task_service = TaskService()


def get_run_type(tasks):
    run_types = set()
    for task in tasks:
        run_types.add(task.execution_type)
    if len(run_types) == 1:
        return run_types.pop()
    return "mixed"


def is_prefect_enable(run_type, run_mode):
    if run_mode == "prefect" and run_type in ["call"]:
        return True
    return False


def get_schedule_state(scheduled_timestamp):
    state = {
        "type": "SCHEDULED",
        "message": "",
        "state_details": {},
    }
    state["state_details"]["scheduled_time"] = datetime.fromtimestamp(
        scheduled_timestamp, timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return state


def get_schedule_time(schedule):
    scheduled_timestamp = None
    if schedule.get("type") == "auto":
        AUTO_MINS = 10
        scheduled_timestamp = (
            int(datetime.now(timezone.utc).timestamp()) + AUTO_MINS * 60
        )
    else:
        calling_date = schedule.get("calling_date")
        calling_time = schedule.get("calling_time")
        if calling_date and calling_time:
            dt_str = f"{calling_date} {calling_time}"
            dt_obj = dateutil.parser.parse(dt_str)
            scheduled_timestamp = int(dt_obj.timestamp())
            if scheduled_timestamp < int(datetime.now(timezone.utc).timestamp()):
                raise HTTPException(
                    status_code=400,
                    detail="Scheduled time must be in the future.",
                )
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid schedule format. 'calling_date' and 'calling_time' are required for manual scheduling.",
            )
    return scheduled_timestamp


@router.post("/create_run/")
async def create_run(request: APIRequestModel):
    # Call the task service to create run and tasks
    task_ids = []
    status = {}
    extra_data = request.data
    tasks = request.tasks
    extra_input = extra_data.get("extra_input")
    execution_type = extra_data.get("execution_type")
    context = extra_data.get("context")
    schedule = extra_data.get("schedule", {})

    run_kargs = {}
    task_kargs = {}
    if not tasks:
        filters = extra_data.get("filters")
        if not filters:
            raise HTTPException(
                status_code=400,
                detail="No tasks provided and filters missing in data",
            )
        space_token = extra_data.get("space_token")
        tasks = await fetch_contact_data(filters, space_token)
        if not tasks:
            raise HTTPException(
                status_code=400,
                detail="No tasks provided and no tasks found in store",
            )

        tasks = [
            Task(
                **{
                    "objective": context,
                    "input_data": {**task, **extra_input},
                    "execution_type": execution_type,
                    "attachments": task.get("attachments", []),
                    "ref_id": task.get("id") or task.get("document_id"),
                }
            )
            for task in tasks
        ]
        print(len(tasks), "tasks fetched from store")
        # tasks = []

    if schedule:
        run_kargs["status"] = "scheduled"
        task_kargs["status"] = "scheduled"
        scheduled_timestamp = get_schedule_time(schedule)
        run_kargs["scheduled_timestamp"] = scheduled_timestamp
        task_kargs["scheduled_timestamp"] = scheduled_timestamp
    # raise HTTPException(
    #     status_code=400,
    #     detail="Invalid schedule format. 'calling_date' and 'calling_time' are required for manual scheduling.",
    # )
    run_type = get_run_type(tasks)
    run_mode = request.run_mode
    if is_prefect_enable(run_type, run_mode):
        run_mode = "prefect"
    else:
        run_mode = "default"
    run = task_service.create_run(
        space_id=request.space_id,
        user=request.user["id"],
        collection_ref=request.collection_ref,
        batch_count=len(request.tasks),
        run_mode=run_mode,
        thread_id=request.thread_id,
        user_org_id=request.org_id,
        user_info=request.user,
        run_type=run_type,
        **run_kargs,
    )

    for task in tasks:
        task_data = {"objective": task.objective}
        result = task_service.add_task(
            run["run_id"],
            task_data,
            request.assignee,
            request.collection_ref,
            request.thread_id,
            task.execution_type,
            input=task.input_data,
            attachments=task.attachments,
            ref_id=task.ref_id,
            space_id=request.space_id,
            user=request.user["id"],
            user_org_id=request.org_id,
            user_info=request.user,
            **task_kargs,
        )

        task_ids.append(result["task_id"])
        status[result["task_id"]] = result["status"]
    print(f'Data Added\n {run["run_id"]} \n {task_ids} \n {status}')
    response = APIResponseModel(run_id=run["run_id"], task_ids=task_ids, status=status)
    if is_prefect_enable(run_type, run_mode):
        data = {"run_id": run["run_id"], "run_type": run_type}
        prefect_kargs = {"parameters": {"job": data}}
        if schedule:
            prefect_kargs["state"] = get_schedule_state(scheduled_timestamp)
        await trigger_deployment("Execute Run", **prefect_kargs)

    return {
        "data": response.model_dump(),
        "message": "Task/Run Created Successfully",
    }


@router.get(
    "/get_runs/", response_model=DynamicResponseModelWithPagination[RunsListModel]
)
async def get_runs(
    request: Request,
    space_id: Optional[str] = None,
    user_id: Optional[str] = None,
    thread_id: Optional[str] = None,
):
    # Call the task service to get runs
    try:
        runs, count = task_service.get_runs(request, space_id, user_id, thread_id)
        return {
            "data": runs,
            "count": count,
            "message": "Runs Fetched Successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/get_tasks/", response_model=DynamicResponseModelWithPagination[TaskListModel]
)
async def get_tasks(
    request: Request,
    space_id: Optional[str] = None,
    user_id: Optional[str] = None,
    thread_id: Optional[str] = None,
):
    try:
        tasks, count = task_service.get_tasks(request, space_id, user_id, thread_id)
        return {
            "data": tasks,
            "count": count,
            "message": "Tasks Fetched Successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/get_run_tasks/{run_id}/",
    response_model=DynamicResponseModelWithPagination[TaskListModel],
)
async def get_run_tasks(
    request: Request,
    run_id: str,
    space_id: Optional[str] = None,
    user_id: Optional[str] = None,
    thread_id: Optional[str] = None,
):
    try:
        tasks, count = task_service.get_run_tasks(
            request, run_id, space_id, user_id, thread_id
        )
        return {
            "data": tasks,
            "count": count,
            "message": "Tasks Fetched Successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
