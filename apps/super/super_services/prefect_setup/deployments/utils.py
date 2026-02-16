from prefect import get_client
from prefect.client.schemas.filters import FlowRunFilter
from super_services.db.services.repository.deployment import (
    get_deployment_config,
    get_all_deployment_configs,
)


async def trigger_deployment(deployment_name, parameters, **kwargs):
    """
    Trigger a deployment using configuration from MongoDB.

    Args:
        deployment_name: Name of the deployment to trigger
        parameters: Parameters to pass to the flow run

    Returns:
        None
    """
    # Fetch deployment config from MongoDB
    db_deployment_config = get_deployment_config(deployment_name)
    if not db_deployment_config:
        raise ValueError(f"Deployment {deployment_name} not found in database")

    # Extract deployment info from DB config
    name = db_deployment_config.get("name")
    flow_name = db_deployment_config.get("flow_name")

    if not flow_name:
        raise ValueError(f"Flow name not found for deployment {deployment_name}")

    # Construct Prefect deployment name filter: {flow_name}/{deployment_name}
    deployment_name_filter = f"{flow_name}/{name}"

    async with get_client() as client:
        deployment = await client.read_deployment_by_name(name=deployment_name_filter)
        if not deployment:
            raise ValueError(f"Deployment {deployment_name} not found in Prefect")
        await client.create_flow_run_from_deployment(
            deployment.id, parameters=parameters, **kwargs
        )
        print(f"✓ Flow Run Created: {deployment_name} (flow: {flow_name})")


def get_available_deployments(work_pool_name=None):
    """
    Get all available deployment configurations from MongoDB.

    Args:
        work_pool_name: Optional filter by work pool name

    Returns:
        List of deployment config dicts
    """
    deployments = get_all_deployment_configs(work_pool_name=work_pool_name)
    return deployments


def get_deployment_metadata(deployment_name):
    """
    Get deployment configuration metadata from MongoDB.

    Args:
        deployment_name: Name of the deployment

    Returns:
        Dict with deployment config (name, docker_image, work_pool_name, tags, concurrency)
    """
    config = get_deployment_config(deployment_name)
    if not config:
        raise ValueError(f"Deployment {deployment_name} not found in database")
    return config


async def check_flow_runs_filter(flow_run_filter=None, *args, **kwargs):
    async with get_client() as client:
        if isinstance(flow_run_filter, dict):
            flow_run_filter = FlowRunFilter(**flow_run_filter)
        flow_runs = await client.read_flow_runs(
            flow_run_filter=flow_run_filter, *args, **kwargs
        )
        return flow_runs


async def fetch_all_concurrency_list():
    async with get_client() as client:
        concurrency_limits = await client.read_concurrency_limits(limit=50, offset=0)
        return concurrency_limits
