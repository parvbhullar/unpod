import aiohttp
from typing import Dict, List, Optional
from libs.api.config import get_settings

settings = get_settings()
from services.task_service.models.deployment import DeploymentConfigModel


async def send_prefect_req(*args, **kwargs):
    """Send a request to Prefect API"""
    kwargs["headers"] = {"Content-Type": "application/json"}
    url = f"{settings.PREFECT_API_URL}/{args[1]}"
    args = (args[0], url) + args[2:]
    async with aiohttp.ClientSession() as session:
        async with session.request(*args, **kwargs) as response:
            return await response.json()


def get_deployment_config(name: str) -> Optional[Dict]:
    """Get deployment config by name"""
    result = DeploymentConfigModel.find_one(name=name)
    return result


def get_all_deployment_configs(work_pool_name: Optional[str] = None) -> List[Dict]:
    """
    Get all deployment configs, optionally filtered by work pool.

    Args:
        work_pool_name: Optional filter by work pool name

    Returns:
        List of deployment config dicts
    """
    query = {}
    if work_pool_name:
        query["work_pool_name"] = work_pool_name

    results = list(DeploymentConfigModel.find(**query))
    return [r.model_dump() for r in results]


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
    filter_url = f"deployments/name/{flow_name}/{name}"

    deployment = await send_prefect_req("GET", filter_url)
    if not deployment:
        raise ValueError(f"Deployment {deployment_name} not found in Prefect")
    deployment_id = deployment.get("id")
    deployment_create_url = f"deployments/{deployment_id}/create_flow_run"
    await send_prefect_req(
        "POST", deployment_create_url, json={"parameters": parameters, **kwargs}
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
