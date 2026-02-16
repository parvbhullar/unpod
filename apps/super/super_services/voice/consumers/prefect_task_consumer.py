import os
import random
import time
import psutil
from typing import Optional
from datetime import datetime, timedelta
from prefect import flow, get_run_logger, task
from prefect.runtime import flow_run
from prefect_dask.task_runners import DaskTaskRunner
from pydantic import BaseModel, Field
from super_services.libs.core.sms import send_sms_msg91
from super_services.prefect_setup.deployments.utils import trigger_deployment
from super_services.prefect_setup.deployments.tag_concurrency import (
    create_run_concurrency_tag,
    delete_run_concurrency_tag,
)

HIGH_PRIORITY = "call-high-priority"


def generate_task_name():
    parameters = flow_run.parameters
    job = parameters["job"]
    if hasattr(job, "model_dump"):
        job = job.model_dump()
    task_id = job["task_id"]
    run_type = job.get("run_type", "normal")
    run_id = job.get("run_id")
    if run_id:
        return f"{run_type}-{run_id}-task-{task_id}"
    return f"{run_type}-task-{task_id}"


def generate_call_run_name():
    parameters = flow_run.parameters
    task_id = parameters["task_id"]
    run_id = parameters["run_id"]
    return f"call-task-{task_id}-{run_id}"


def generate_run_flow_name():
    parameters = flow_run.parameters
    job = parameters["job"]
    run_id = job.get("run_id")
    run_type = job.get("run_type")
    retry = job.get("retry", 0)
    return f"run-flow-{run_type}-{run_id}-{retry}"


def generate_sent_retry_sms_flow_name():
    parameters = flow_run.parameters
    task_id = parameters["task_id"]
    return f"sent_retry_sms-{task_id}"


def generate_reschedule_run_flow_name():
    parameters = flow_run.parameters
    job = parameters["job"]
    run_id = job.get("run_id")
    retry = job.get("retry", 0)
    return f"reschedule_run-{run_id}-retry-{retry}"


@task(
    description="Execute Call Activity (Sync wrapper for Dask)",
    tags=["execute_call", "sync"],
    log_prints=True,
)
def execute_call_activity_sync_consumer(message: dict) -> dict:
    from .voice_task_consumer import _process_task_worker

    _process_task_worker(message, "normal", 20)


@flow(
    name="Execute Call Flow Consumer",
    description="Process Call jobs",
    flow_run_name=generate_call_run_name,
)
def execute_call_flow_consumer(
    run_id: str,
    task_id: str,
    agent_id: str,
    data: dict,
    instructions: str = None,
    model_config_data: dict = None,
    run_type=None,
    index=0,
):
    from super.app.providers.factory import CallProviderFactory

    message = {
        "run_id": run_id,
        "task_id": task_id,
        "agent_id": agent_id,
        "data": data,
        "instructions": instructions,
        "model_config": model_config_data,
    }
    call_provider = CallProviderFactory.get_provider_type(data)
    run_tag = f"execute_{run_type or 'call'}"
    random_sleep = random.randint(3, 8) * (index + 1)
    if random_sleep > 20:
        random_sleep = random_sleep // 2
    time.sleep(random_sleep)
    execute_call_activity_sync_consumer.with_options(
        name=f"execute_call_task_{task_id}",
        tags=[f"call_{call_provider}", run_tag],
    )(message)


@task
def process_task(*args, **kwargs):
    """Wrapper task for executing call flow."""
    try:
        execute_call_flow_consumer(*args, **kwargs)
    except Exception as ex:
        logger = get_run_logger()
        logger.error(f"Process task failed: {str(ex)}")
        raise


@flow(
    name="Check Reschedule Run",
    description="Check and reschedule run flow",
    flow_run_name=generate_reschedule_run_flow_name,
)
async def check_reschedule_run(job):
    # parameters = flow_run.parameters
    # job = parameters["job"]
    run_id = job.get("run_id")
    retry = job.get("retry", 0)
    run_type = job.get("run_type")
    attempt = flow_run.run_count
    logger = get_run_logger()
    from super_services.orchestration.task.task_service import TaskService

    task_service = TaskService()
    tasks = task_service.get_pending_tasks(run_id)
    logger.info(f"Reschedule run {run_id} with {len(tasks)} tasks, {retry}, {attempt}")
    if len(tasks) and retry < 3:
        # raise Exception("Run has pending tasks")
        from prefect.states import Scheduled

        next_5min = datetime.utcnow() + timedelta(minutes=5)
        flow_name = f"run-flow-{run_type}-{run_id}-{retry}"
        await trigger_deployment(
            "Execute Run",
            {"job": {"run_id": run_id, "retry": retry + 1, "run_type": run_type}},
            state=Scheduled(scheduled_time=next_5min),
            name=flow_name,
        )
    return True


@flow(
    name="Process Run Flow",
    description="Process Run jobs",
    flow_run_name=generate_run_flow_name,
    task_runner=DaskTaskRunner(cluster_kwargs={"n_workers": psutil.cpu_count()}),
    # log_prints=True,
)
async def process_run_flow(job):
    from super_services.orchestration.task.task_service import TaskService

    # parameters = flow_run.parameters
    # job = parameters["job"]
    run_id = job.get("run_id")
    retry = job.get("retry", 0)
    logger = get_run_logger()

    logger.info(f"Processing run {run_id} with retry {retry}")

    task_service = TaskService()
    run_status = task_service.get_run_status(run_id)
    if run_status.get("run").get("status") == "completed":
        logger.info(f"Run {run_id} is already completed")
        return
    run_type = run_status.get("run").get("run_type")
    if run_type not in ["call"]:
        logger.info(f"Run {run_id} is of type {run_type}, skipping processing")
        return
    logger.info(
        f"Run {run_id} is in {run_status.get('run').get('status')}, processing tasks"
    )
    tasks = task_service.get_pending_tasks(
        run_id, run_status=run_status.get("run").get("status")
    )
    logger.info(f"Processing run {run_id} with {len(tasks)} tasks")

    # Create dynamic concurrency tag for this run (max 8 concurrent tasks)
    run_tag = f"run_{run_id}"
    RUN_WISE_CONCURRENCY = os.environ.get("RUN_WISE_CONCURRENCY", 10)
    run_wise_concurrency = min(int(RUN_WISE_CONCURRENCY), len(tasks))
    await create_run_concurrency_tag(run_id, concurrency_limit=run_wise_concurrency)
    logger.info(
        f"Created concurrency tag '{run_tag}' with limit {run_wise_concurrency}"
    )

    try:
        # tasks_results = []
        for index, task in enumerate(tasks):
            task_id = task.get("task_id")
            task_flow_name = f"{run_type}-{run_id}-task-{task_id}"
            extra_kargs = {}
            if len(tasks) < 5:
                extra_kargs["work_queue_name"] = HIGH_PRIORITY
            await trigger_deployment(
                "Execute-Task",
                {
                    "job": {
                        "task_id": task_id,
                        "run_type": run_type,
                        "run_id": run_id,
                    }
                },
                tags=[run_tag],
                name=task_flow_name,
                **extra_kargs,
            )
            logger.info(f"Triggered task {task_id} for run {run_id} index, {index+1}")
            time.sleep(0.5)
        #     tasks_results.append(
        #         process_task.with_options(
        #             name=f"process_task_{task_id}",
        #             tags=[run_tag],
        #         ).submit(
        #             run_id=run_id,
        #             task_id=task.get("task_id"),
        #             agent_id=task.get("assignee"),
        #             data=task.get("input"),
        #             instructions=task.get("task", {}).get("objective"),
        #             model_config_data={},
        #             run_type=run_type,
        #             index=index,
        #         )
        #     )
        # for task_result in tasks_results:
        #     task_result.result(raise_on_failure=True)
        # logger.info(f"Completed processing run {run_id}")
    finally:
        logger.info(f"All tasks triggered for run {run_id}")
        # Delete dynamic concurrency tag after all tasks complete
        # await delete_run_concurrency_tag(run_id)
        # logger.info(f"Deleted concurrency tag '{run_tag}'")


class TaskJob(BaseModel):
    task_id: str
    run_type: str
    retry: Optional[int] = Field(default=0)
    run_id: Optional[str] = Field(default=None)


@flow(
    name="Process Task Flow",
    description="Process Task job",
    flow_run_name=generate_task_name,
    log_prints=True,
)
def process_task_flow(job: TaskJob):
    from super_services.orchestration.task.task_service import TaskService
    from super.app.providers.factory import CallProviderFactory

    task_service = TaskService()
    task = task_service.get_task(job.task_id)
    logger = get_run_logger()
    if not task:
        logger.error(f"Task {job.task_id} not found")
        return
    run_id = task.get("run_id")
    task_id = task.get("task_id")
    agent_id = task.get("assignee")
    data = task.get("input")
    instructions = task.get("task", {}).get("objective")
    model_config_data = {}
    message = {
        "run_id": run_id,
        "task_id": task_id,
        "agent_id": agent_id,
        "data": data,
        "instructions": instructions,
        "model_config": model_config_data,
    }
    call_provider = CallProviderFactory.get_provider_type(data)
    run_tag = f"execute_{job.run_type or 'call'}"
    run_based_tag = f"run_{run_id}"
    execute_call_activity_sync_consumer.with_options(
        name=f"execute_call_task_{task_id}",
        tags=[f"call_{call_provider}", run_tag, run_based_tag],
    )(message)
    logger.info(f"Processed task {task_id} for run {run_id}")


@flow(
    name="Run Cleanup Flow",
    description="Run Cleanup Flow",
    flow_run_name=generate_run_flow_name,
)
async def process_run_cleanup_flow(job):
    from super_services.orchestration.task.task_service import TaskService

    run_id = job.get("run_id")
    logger = get_run_logger()

    task_service = TaskService()
    run_obj = task_service.get_run(run_id)
    if not run_obj:
        logger.info(f"Run {run_id} not found for cleanup")
        return
    run_status = run_obj.get("status")
    if run_status in ["completed", "failed", "partially_completed"]:
        logger.info(f"Starting cleanup for run {run_id} with status {run_status}")
        try:
            await delete_run_concurrency_tag(run_id)
        except Exception as ex:
            logger.error(f"Error deleting concurrency tag for run {run_id}: {str(ex)}")
    else:
        logger.info(f"Run {run_id} is in {run_status}, skipping cleanup")


@flow(
    name="Send Retry SMS",
    description="Send Retry SMS to user",
    flow_run_name=generate_sent_retry_sms_flow_name,
)
async def sent_retry_sms(task_id: str, data: dict):
    from super_services.orchestration.task.task_service import TaskService
    from super_services.db.services.models.task import CallRetrySmsModel

    logger = get_run_logger()
    task_service = TaskService()
    task = task_service.get_task(task_id)
    if not task:
        logger.error(f"Task {task_id} not found")
        return
    temp_id = data.get("temp_id")
    contact_number = data.get("contact_number")
    kargs = data.get("kargs", {})
    res = await send_sms_msg91(contact_number, temp_id, **kargs)
    logger.info(f"Res - {res.text}")
    logger.info(f"Sent retry sms to {contact_number} for task {task_id}")
    CallRetrySmsModel._get_collection().update_one(
        {"task_id": task_id, "status": "processing"},
        {"$set": {"status": "completed", "response": res.text}},
    )
    return True
