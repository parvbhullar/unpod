import asyncio

from super.core.voice.workflows.post_call import PostCallWorkflow
from super_services.db.services.models.task import TaskModel


async def execute(task_id):
    task = TaskModel.get(task_id=task_id)

    from .dspy_config import get_dspy_lm

    lm = get_dspy_lm()
    post_call_input_data = {
        "task_id": task_id,
        "instructions": "",
        "input_data": task.input,
        "output": "",
        "call_end_time": "",
    }
    from super_services.voice.models.config import ModelConfig
    from super.core.voice.schema import UserState

    config = ModelConfig().get_config(task.assignee)

    workflow_handler = PostCallWorkflow(
        model_config=config,
        transcript=task.output.get("transcript", ""),
        token=task.input.get("token", None),
        document_id=task.input.get("document_id", None),
        data=post_call_input_data,
        lm=lm,
        user_state=UserState(call_status="notConnected",model_config=config,contact_number="8847348129"),
    )
    post_call_result = await workflow_handler.execute()

    return post_call_result


if __name__ == "__main__":
    res = asyncio.run(execute("Tefe4015f78de11f082ac156368e7acc4"))

    print(f"{'='*100} \n\n post_call_result: \n\n {res} \n\n {'='*100}")
