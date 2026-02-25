from typing import Optional

from prefect import get_client
from prefect.client.schemas.filters import FlowRunFilter

from super_services.prefect_setup.deployments.create_deployments import (
    load_local_configs,
)


def _get_config_from_db(name: str) -> Optional[dict]:
    """Try fetching deployment config from MongoDB."""
    try:
        from super_services.db.services.repository.deployment import (
            get_deployment_config,
        )

        return get_deployment_config(name)
    except Exception:
        return None


def _get_all_configs_from_db(
    work_pool_name: Optional[str] = None,
) -> list[dict]:
    """Try fetching all deployment configs from MongoDB."""
    try:
        from super_services.db.services.repository.deployment import (
            get_all_deployment_configs,
        )

        return get_all_deployment_configs(work_pool_name=work_pool_name)
    except Exception:
        return []


def _get_config(name: str) -> Optional[dict]:
    """Get deployment config from MongoDB, falling back to local JSON."""
    config = _get_config_from_db(name)
    if config:
        return config

    # Fallback to local JSON
    for cfg in load_local_configs():
        if cfg.get("name") == name:
            return cfg
    return None


async def trigger_deployment(deployment_name, parameters, **kwargs):
    """Trigger a deployment using config from MongoDB or local JSON."""
    config = _get_config(deployment_name)
    if not config:
        raise ValueError(
            f"Deployment {deployment_name} not found in DB or local JSON"
        )

    name = config.get("name")
    flow_name = config.get("flow_name")

    if not flow_name:
        raise ValueError(
            f"Flow name not found for deployment {deployment_name}"
        )

    deployment_name_filter = f"{flow_name}/{name}"

    async with get_client() as client:
        deployment = await client.read_deployment_by_name(
            name=deployment_name_filter
        )
        if not deployment:
            raise ValueError(
                f"Deployment {deployment_name} not found in Prefect"
            )
        await client.create_flow_run_from_deployment(
            deployment.id, parameters=parameters, **kwargs
        )
        print(f"Flow Run Created: {deployment_name} (flow: {flow_name})")


def get_available_deployments(
    work_pool_name: Optional[str] = None,
) -> list[dict]:
    """Get all deployment configs from MongoDB or local JSON fallback."""
    configs = _get_all_configs_from_db(work_pool_name=work_pool_name)
    if configs:
        return configs

    # Fallback to local JSON
    all_configs = load_local_configs()
    if work_pool_name:
        return [
            c
            for c in all_configs
            if c.get("work_pool_name") == work_pool_name
        ]
    return all_configs


def get_deployment_metadata(deployment_name: str) -> dict:
    """Get deployment config from MongoDB or local JSON fallback."""
    config = _get_config(deployment_name)
    if not config:
        raise ValueError(
            f"Deployment {deployment_name} not found in DB or local JSON"
        )
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
        concurrency_limits = await client.read_concurrency_limits(
            limit=50, offset=0
        )
        return concurrency_limits
