from super_services.prefect_setup.deployments.create_deployments import (
    create_deployment,
)
from super_services.prefect_setup.deployments.deployment_config import (
    DOCKER_IMAGES,
    CALL_WORK_POOL,
)
from super_services.orchestration.task.deployments.env_config import CALL_ENVS
from super_services.voice.consumers.prefect_task_consumer import (
    process_run_flow,
    check_reschedule_run,
    process_task_flow,
    process_run_cleanup_flow,
    sent_retry_sms,
)
from super_services.orchestration.cron_jobs.post_call import post_call_flow
from super_services.orchestration.cron_jobs.eval_testing import test_agent_evals
# from super_services.orchestration.cron_jobs.calls_cron import inbound_calls_flow
# from super_services.orchestration.cron_jobs.recordings_cron import recordings_cron

DEPLOYMENT_CONFIGURATIONS = [
    {
        "name": "Execute Run",
        "flow": process_run_flow,
        "docker_image": DOCKER_IMAGES["call_task"],
        "work_pool_name": CALL_WORK_POOL,
        "tags": ["call"],
        "concurrency": 10,
        "job_variables": {"env": CALL_ENVS},
    },
    {
        "name": "Check Reschedule Run",
        "flow": check_reschedule_run,
        "docker_image": DOCKER_IMAGES["call_task"],
        "work_pool_name": CALL_WORK_POOL,
        "tags": ["call"],
        "concurrency": 10,
        "job_variables": {"env": CALL_ENVS},
    },
    {
        "name": "Execute-Task",
        "flow": process_task_flow,
        "docker_image": DOCKER_IMAGES["call_task"],
        "work_pool_name": CALL_WORK_POOL,
        "tags": ["call"],
        "concurrency": 13,
        "job_variables": {"env": CALL_ENVS},
    },
    {
        "name": "Execute-Run-Cleanup",
        "flow": process_run_cleanup_flow,
        "docker_image": DOCKER_IMAGES["call_task"],
        "work_pool_name": CALL_WORK_POOL,
        "tags": ["call"],
        "concurrency": 6,
        "job_variables": {"env": CALL_ENVS},
    },
    {
        "name": "Post-Call-Flow",
        "flow": post_call_flow,
        "docker_image": DOCKER_IMAGES["call_task"],
        "work_pool_name": CALL_WORK_POOL,
        "tags": ["call"],
        "concurrency": 2,
        "job_variables": {"env": CALL_ENVS},
    },
    {
        "name": "Sent-Retry-SMS",
        "flow": sent_retry_sms,
        "docker_image": DOCKER_IMAGES["call_task"],
        "work_pool_name": CALL_WORK_POOL,
        "tags": ["sms", "call"],
        "concurrency": 10,
        "job_variables": {"env": CALL_ENVS},
    },
    {
        "name": "Agent-Evals-Test",
        "flow": test_agent_evals,
        "docker_image": DOCKER_IMAGES["call_task"],
        "work_pool_name": CALL_WORK_POOL,
        "tags": ["evals", "agent_testing"],
        "concurrency": 10,
        "job_variables": {"env": CALL_ENVS},
    }
    # {
    #     "name": "Inbound Calls",
    #     "flow": inbound_calls_flow,
    #     "docker_image": DOCKER_IMAGES["call_task"],
    #     "work_pool_name": CALL_WORK_POOL,
    #     "tags": ["call"],
    #     "concurrency": 10,
    # },
    # {
    #     "name": "Call Recordings",
    #     "flow": recordings_cron,
    #     "docker_image": DOCKER_IMAGES["call_task"],
    #     "work_pool_name": CALL_WORK_POOL,
    #     "tags": ["call"],
    #     "concurrency": 10,
    # }
]

if __name__ == "__main__":
    # Run the async function
    create_deployment(DEPLOYMENT_CONFIGURATIONS)
