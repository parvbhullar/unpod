import uuid
import asyncio
import requests
from typing import Optional, Dict, Any

from humanfriendly.terminal import output
from super_services.db.services.models.task import (
    RunModel,
    TaskModel,
    TaskExecutionLogModel,
    CallRetrySmsModel,
)
from super_services.db.services.schemas.task import TaskStatusEnum
from datetime import datetime

from dotenv import load_dotenv
from super.core.voice.schema import TaskData


load_dotenv()
import os


async def _run_sync_db_op(func, *args, **kwargs):
    """Run a synchronous DB operation in a thread pool to avoid blocking."""
    return await asyncio.to_thread(func, *args, **kwargs)


async def create_run_async(task_data: TaskData) -> str:
    """Create a run record asynchronously."""
    run_id = f"R{uuid.uuid1().hex}"

    await _run_sync_db_op(
        RunModel.save_single_to_db,
        {
            "run_id": run_id,
            "space_id": task_data.space_id,
            "batch_count": 1,
            "collection_ref": task_data.collection_ref,
            "run_mode": "dev",
            "thread_id": task_data.thread_id,
            "owner_org_id": "",
            "status": TaskStatusEnum.in_progress,
            "user": task_data.user_id,
        },
    )

    return run_id


async def create_task_async(task_data: TaskData) -> str:
    """Create a task record asynchronously."""
    task_id = f"T{uuid.uuid1().hex}"

    data = {
        "task_id": task_id,
        "space_id": task_data.space_id,
        "user": task_data.user_id,
        "run_id": task_data.run_id,
        "thread_id": task_data.thread_id,
        "collection_ref": task_data.collection_ref,
        "task": {},
        "assignee": task_data.assignee,
        "status": TaskStatusEnum.in_progress,
        "execution_type": task_data.execution_type,
        "retry_attempt": 0,
        "last_status_change": datetime.utcnow().isoformat(),
        "input": task_data.input,
    }

    await _run_sync_db_op(TaskModel.save_single_to_db, data)

    return task_id


# Keep synchronous versions for backward compatibility
def create_run(task_data: TaskData) -> str:
    """Create a run record synchronously (legacy)."""
    run_id = f"R{uuid.uuid1().hex}"

    RunModel.save_single_to_db(
        {
            "run_id": run_id,
            "space_id": task_data.space_id,
            "batch_count": 1,
            "collection_ref": task_data.collection_ref,
            "run_mode": "dev",
            "thread_id": task_data.thread_id,
            "owner_org_id": "",
            "status": TaskStatusEnum.in_progress,
            "user": task_data.user_id,
        }
    )

    return run_id


def create_task(task_data: TaskData) -> str:
    """Create a task record synchronously (legacy)."""
    task_id = f"T{uuid.uuid1().hex}"

    data = {
        "task_id": task_id,
        "space_id": task_data.space_id,
        "user": task_data.user_id,
        "run_id": task_data.run_id,
        "thread_id": task_data.thread_id,
        "collection_ref": task_data.collection_ref,
        "task": {},
        "assignee": task_data.assignee,
        "status": TaskStatusEnum.in_progress,
        "execution_type": task_data.execution_type,
        "retry_attempt": 0,
        "last_status_change": datetime.utcnow().isoformat(),
        "input": task_data.input,
    }

    TaskModel.save_single_to_db(data)

    return task_id


async def create_task_and_thread(task_data: TaskData) -> Dict[str, str]:
    """
    Create task and thread - OPTIMIZED VERSION.

    Key optimizations:
    1. Run + Task creation in parallel (they're independent)
    2. Thread creation deferred to background (not blocking call start)
    3. Execution log deferred to background
    """
    from time import perf_counter

    _start = perf_counter()

    # Generate IDs upfront
    run_id = f"R{uuid.uuid1().hex}"
    task_id = f"T{uuid.uuid1().hex}"

    # Prepare data for parallel creation
    run_data = {
        "run_id": run_id,
        "space_id": task_data.space_id,
        "batch_count": 1,
        "collection_ref": task_data.collection_ref,
        "run_mode": "dev",
        "thread_id": task_data.thread_id,
        "owner_org_id": "",
        "status": TaskStatusEnum.in_progress,
        "user": task_data.user_id,
    }

    task_db_data = {
        "task_id": task_id,
        "space_id": task_data.space_id,
        "user": task_data.user_id,
        "run_id": run_id,  # Use the pre-generated run_id
        "thread_id": task_data.thread_id,
        "collection_ref": task_data.collection_ref,
        "task": {},
        "assignee": task_data.assignee,
        "status": TaskStatusEnum.in_progress,
        "execution_type": task_data.execution_type,
        "retry_attempt": 0,
        "last_status_change": datetime.utcnow().isoformat(),
        "input": task_data.input,
    }

    # Run both DB operations in parallel
    await asyncio.gather(
        _run_sync_db_op(RunModel.save_single_to_db, run_data),
        _run_sync_db_op(TaskModel.save_single_to_db, task_db_data),
    )

    print(f"\n created task with id {task_id} \n")

    # Defer thread creation and execution log to background
    # These don't block the call from starting
    asyncio.create_task(_create_thread_and_log_background(task_id, task_data))

    _elapsed = (perf_counter() - _start) * 1000
    print(f"[TIMING] create_task_and_thread (optimized): {_elapsed:.0f}ms")

    return {
        "thread_id": "",  # Thread created in background
        "task_id": task_id,
        "run_id": run_id,
    }


async def _create_thread_and_log_background(task_id: str, task_data: TaskData) -> None:
    """Background task to create thread and log execution."""
    try:
        from super_services.voice.common.threads import create_thread_async

        thread_id = await create_thread_async(task_id)
        task_data.thread_id = thread_id

        # Update task with thread_id in background
        await _run_sync_db_op(
            TaskModel.update_one, {"task_id": task_id}, {"thread_id": str(thread_id)}
        )

        await save_execution_log(
            task_id,
            "inbound call executed",
            TaskStatusEnum.completed,
            "created new task and run alongside thread",
        )
    except Exception as e:
        print(f"[BACKGROUND] Thread/log creation failed: {e}")


async def save_execution_log(
    task_id: str, step: str, status: str, output: Any, error: Optional[str] = None
) -> None:
    """Save execution log asynchronously."""
    if not task_id:
        print(f"[EXECUTION_LOG] Skipping - no task_id provided")
        return

    if isinstance(output, str):
        output = {"data": output}

    exec_id = f"TE{uuid.uuid1().hex}"

    try:
        # Get task info in thread pool
        task = await _run_sync_db_op(TaskModel.get, task_id=task_id)
    except Exception as e:
        print(f"[EXECUTION_LOG] Task not found for task_id={task_id}: {e}")
        return

    exec_log_data = {
        "task_exec_id": exec_id,
        "task_id": task.task_id,
        "run_id": task.run_id,
        "executor_id": "default",
        "status": status,
        "input": task.input,
        "output": {
            "step": step,
            "data": output,
        },
        "space_id": task.space_id,
        "data": {},
    }
    if error:
        exec_log_data["output"] = {"error": str(error)}
    try:
        print("creating execution log")
        await _run_sync_db_op(TaskExecutionLogModel.save_single_to_db, exec_log_data)
    except Exception as e:
        print("creating execution log", str(e))


async def create_collection_doc(user_state, payload):
    STORE_SERVICE_URL = os.getenv("STORE_SERVICE_URL")

    url = f"{STORE_SERVICE_URL}/api/v1/store/collection-doc-data/{user_state.token}/"
    try:
        response = requests.post(url, json=payload)

        if response.status_code == 200:
            return response.json().get("data").get("document_id", "")
        else:
            return ""
    except Exception as e:
        return ""


async def get_doc_id_from_number(number, token):
    STORE_SERVICE_URL = os.getenv("STORE_SERVICE_URL")

    url = f"{STORE_SERVICE_URL}/api/v1/store/collection-connector-data/{token}/"
    try:
        response = requests.get(url)

        if number.startswith("0"):
            number = number[1:]

        if response.status_code == 200:
            data = response.json()["data"]["data"]

            for doc in data:
                if number in doc.get("contact_number", "") or number in doc.get(
                    "number", ""
                ):
                    return doc.get("document_id"), doc.get("name")

        return "", ""

    except Exception as e:
        return "", ""


async def create_scheduled_task(task_id, time, max_calls: int = 3):
    if not task_id:
        return

    print(f"[TIMING] Creating scheduled task {task_id}")

    if isinstance(time, str):
        time = datetime.fromisoformat(time)
    try:
        task = TaskModel.get(task_id=task_id)

        followup_count = task.output.get("followup_count")

        if followup_count:
            followup_count = int(followup_count)
            followup_count += 1
        else:
            followup_count = 1

        if followup_count >= max_calls:
            print(
                f"skipping task creation: followup_count={followup_count} "
                f">= max_calls={max_calls}"
            )
            return

        # Idempotency: check for existing scheduled follow-up for same task/contact scope.
        dedup_query = {
            "status": TaskStatusEnum.scheduled,
            "assignee": task.assignee,
        }
        if getattr(task, "ref_id", None):
            dedup_query["ref_id"] = task.ref_id
        else:
            dedup_query["output.referenced_task"] = task.task_id

        existing = TaskModel._get_collection().find_one(dedup_query)
        if existing:
            print(
                f"[DEDUP] Scheduled task already exists: {existing.get('task_id')}"
            )
            return {
                "task_id": existing.get("task_id"),
                "time": time,
                "deduplicated": True,
            }

        new_task_id = f"T{uuid.uuid1().hex}"

        data = {
            "task_id": new_task_id,
            "space_id": task.space_id,
            "user": task.user if task.user else "",
            "run_id": task.run_id,
            "thread_id": task.thread_id if task.thread_id else "",
            "collection_ref": task.collection_ref if task.collection_ref else "",
            "task": {},
            "assignee": task.assignee,
            "status": TaskStatusEnum.scheduled,
            "execution_type": "call",
            "output": {
                "scheduled_time": str(time),
                "followup_count": followup_count,
                "referenced_task": task.task_id,
            },
            "input": task.input,
            "retry_attempt": 0,
            "scheduled_timestamp": int(time.timestamp()),
        }

        TaskModel.save_single_to_db(data)

        print(f"scheduled call {new_task_id}")

        return {"task_id": new_task_id, "time": time}

    except Exception as e:
        print(f"error rescheduling call {str(e)}")
        return


def schedule_redial_task(task_id, time, transcript):
    if not task_id:
        return False

    if isinstance(time, str):
        time = datetime.fromisoformat(time)
    redial_count = 1
    try:
        task = TaskModel.get(task_id=task_id)
        task_input = task.input
        try:
            if task_input.get("redial_count"):
                redial_count += task_input.get("redial_count")

        except Exception as e:
            print(e)

        if redial_count > 2:
            return False

        task_input["redial_count"] = redial_count
        task_input["transcript"] = transcript

        updated_data = {
            "status": TaskStatusEnum.scheduled,
            "input": task_input,
            "scheduled_timestamp": int(time.timestamp()),
        }

        TaskModel.update_one({"task_id": task.task_id}, updated_data)

        return True

    except Exception as e:
        print(f"error rescheduling call{str(e)}")
        return False


def get_temp_id(assignee):
    if assignee and (assignee.startswith("bob-card") or assignee.startswith("bobcard")):
        return os.environ.get("BOB_TEMP", "695b6bb36ca4495d4463e8d6"), False

    return os.getenv("DEFAULT_TEMP", "697a1118081ed531e53d20ee"), True


def get_agent_number(user_state):
    config = user_state.model_config
    if not config:
        return ""

    if not isinstance(user_state.extra_data, dict):
        user_state.extra_data = {}

    trunk_id = user_state.extra_data.get("trunk_id")
    try:
        trunks = config.get("telephony", [])

        if not isinstance(trunks, list):
            return ""

        for trunk in trunks:
            ass_trunk = trunk.get("association", {}).get("trunk_id", "")
            if ass_trunk == trunk_id:
                number = trunk.get("number", "")
                if number.startswith("+91"):
                    number.replace("+91", "0")
                    return number

        return ""

    except Exception as e:
        print(f"unable to get agent number {str(e)}")
        return ""


def get_brand_name(space_id):
    query = """
    select sporg.name as brand_name from space_spaceorganization as sporg
    Left join space_space as sp on sp.space_organization_id= sporg.id
    where sp.id = %(space_id)s
    """

    from super_services.libs.core.db import executeQuery

    try:
        res = executeQuery(query, {"space_id": space_id})

        return res.get("brand_name")

    except Exception as e:
        return ""


async def send_retry_sms(user_state, task_id, assignee):
    from super_services.prefect_setup.deployments.utils import (
        trigger_deployment,
    )
    from super_services.libs.core.timezone_utils import normalize_phone_number

    TEMP_ID, is_default = get_temp_id(assignee)

    task = TaskModel.get(task_id=task_id)
    redial_count = 0
    task_input = task.input
    task_output = task.output if isinstance(task.output, dict) else {}

    try:
        if task_output.get("followup_count") is not None:
            redial_count += int(task_output.get("followup_count"))
        elif task_input.get("followup_count") is not None:
            redial_count += int(task_input.get("followup_count"))

    except Exception as e:
        print(e)

    if redial_count < 2:
        return

    try:
        contact_number = normalize_phone_number(user_state.contact_number)
    except Exception as e:
        contact_number = ""

    if contact_number and contact_number.startswith("+91"):
        if assignee:
            contact_number = contact_number.replace("+91", "")
            print(f"Sending SMS to {contact_number} for task {task_id}")

            agent_number = get_agent_number(user_state)

            kargs = {
                "call_retry": redial_count + 1,
                "number": agent_number,
            }

            if is_default:
                kargs["brand_name"] = get_brand_name(task.space_id)

            parameters = {
                "task_id": task_id,
                "data": {
                    "kargs": kargs,
                    "contact_number": contact_number,
                    "temp_id": TEMP_ID,
                },
            }
            flow_name = f"sent_retry_sms-{task_id}"

            await trigger_deployment("Sent-Retry-SMS", parameters, name=flow_name)

            call_details = {
                "task_id": task_id,
                "customer_name": user_state.user_name,
                "contact_number": contact_number,
                "assignee": assignee,
                "start_time": user_state.start_time,
                "end_time": user_state.end_time,
                "call_status": user_state.call_status,
            }

            CallRetrySmsModel.save_single_to_db(
                {
                    "task_id": task_id,
                    "contact_number": contact_number,
                    "temp_id": TEMP_ID,
                    "kargs": kargs,
                    "input_data": {"call": call_details},
                    "status": TaskStatusEnum.processing,
                }
            )
        else:
            print("Not a Allowed assignee, skipping SMS")
    else:
        print("Not a valid indian contact number")
        return False


def update_task_with_status(task_id, status):
    try:
        task =TaskModel.get(task_id=task_id)
        output=task.output
        output["call_status"] = status

        TaskModel.update_one({"task_id":task_id}, {"output":output})
    except Exception as e:
        print(e)
        pass


async def test():
    # res = schedule_redial_task(
    #     "Tefe4015f78de11f082ac156368e7acc4", datetime.utcnow(), []
    # )

    print(get_brand_name(521))


if "__main__" == __name__:
    import asyncio

    asyncio.run(test())
