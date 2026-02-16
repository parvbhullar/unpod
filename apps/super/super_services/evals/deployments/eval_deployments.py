"""
Deployment configuration for eval generation flows.
"""
from super_services.prefect_setup.deployments.create_deployments import (
    create_deployment,
)
from super_services.prefect_setup.deployments.deployment_config import (
    DOCKER_IMAGES,
    CALL_WORK_POOL,
)
from super_services.orchestration.task.deployments.env_config import CALL_ENVS
from super_services.evals.flows.eval_generation_flow import (
    generate_agent_evals_flow,
)


EVAL_DEPLOYMENT_CONFIGURATIONS = [
    {
        "name": "Generate-Agent-Evals",
        "flow": generate_agent_evals_flow,
        "docker_image": DOCKER_IMAGES["call_task"],
        "work_pool_name": CALL_WORK_POOL,
        "tags": ["evals"],
        "concurrency": 5,
        "job_variables": {"env": CALL_ENVS},
    },
]


if __name__ == "__main__":
    create_deployment(EVAL_DEPLOYMENT_CONFIGURATIONS)
