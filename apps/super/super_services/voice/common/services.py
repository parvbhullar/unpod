import uuid
from super_services.db.services.models.task import (
    TaskModel,
    TaskExecutionLogModel,
)


async def save_execution_log(task_id, step, status, output, error=None):
    if isinstance(output, str):
        output = {"data": output}

    exec_id = f"TE{uuid.uuid1().hex}"
    task = TaskModel.get(task_id=task_id)

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
        exec_status = TaskExecutionLogModel.save_single_to_db(exec_log_data)
    except Exception as e:
        print("creating execution log", str(e))
