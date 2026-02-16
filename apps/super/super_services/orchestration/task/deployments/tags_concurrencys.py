import asyncio
from super_services.prefect_setup.deployments.tag_concurrency import (
    create_tag_concurrency_tasks,
)

TASK_CONCURRENCY = [
    {
        "tag_name": f"execute_call",
        "concurrency_limit": 20,
    },
    {
        "tag_name": f"call_vapi",
        "concurrency_limit": 10,
    },
    {
        "tag_name": f"call_pipecat",
        "concurrency_limit": 10,
    },
    {
        "tag_name": f"call_livekit",
        "concurrency_limit": 10,
    },
]

if __name__ == "__main__":
    asyncio.run(create_tag_concurrency_tasks(TASK_CONCURRENCY))
