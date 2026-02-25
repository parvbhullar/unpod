import json
import os
import traceback
from typing import Any

from prefect import deploy
from prefect.runner.storage import LocalStorage

# Local JSON fallback path (next to this file)
_CONFIGS_JSON = os.path.join(os.path.dirname(__file__), "deployment_configs.json")


def _save_configs_local(deployment_confs: list[dict[str, Any]]) -> list[dict]:
    """Save deployment configs to a local JSON file (always works)."""
    configs: list[dict] = []
    for dep in deployment_confs:
        flow = dep.get("flow")
        flow_name = flow.name if flow and hasattr(flow, "name") else ""
        configs.append(
            {
                "name": dep["name"],
                "flow_name": flow_name,
                "docker_image": dep.get("docker_image", ""),
                "work_pool_name": dep.get("work_pool_name", ""),
                "tags": dep.get("tags", []),
                "concurrency": dep.get("concurrency", 10),
            }
        )
    with open(_CONFIGS_JSON, "w") as f:
        json.dump(configs, f, indent=2)
    print(f"Saved {len(configs)} deployment configs to {_CONFIGS_JSON}")
    return configs


def _sync_to_db(deployment_confs: list[dict[str, Any]]) -> None:
    """Best-effort sync to MongoDB. Warns on failure, never blocks."""
    try:
        from super_services.db.services.repository.deployment import (
            sync_deployment_configs_to_db,
        )

        sync_deployment_configs_to_db(deployment_confs)
    except Exception:
        print("Warning: Failed to sync deployment configs to MongoDB (non-blocking)")
        traceback.print_exc()


def load_local_configs() -> list[dict]:
    """Load deployment configs from local JSON fallback."""
    if not os.path.exists(_CONFIGS_JSON):
        return []
    with open(_CONFIGS_JSON) as f:
        return json.load(f)


def create_deployment(deployment_confs):
    # Step 1: Always save locally
    _save_configs_local(deployment_confs)

    # Step 2: Best-effort DB sync
    _sync_to_db(deployment_confs)

    # Step 3: Register with Prefect (always runs)
    docker_image_dict = {}
    for deployment in deployment_confs:
        docker_image = deployment.get("docker_image", None)
        if docker_image in [None]:
            docker_image = ""

        flow = deployment["flow"]
        workpool_name = deployment.get("work_pool_name", "common-pool")
        kwargs = {
            "name": deployment["name"],
            "work_pool_name": deployment.get("work_pool_name", "common-pool"),
            "job_variables": deployment["job_variables"],
            "interval": deployment.get("interval", None),
            "tags": deployment.get("tags", []),
            "concurrency_limit": deployment.get("concurrency", None),
            "schedule": deployment.get("schedule", None),
        }

        # if ENVIRONMENT == 'local':
        deploy_obj = flow.to_deployment(**kwargs)
        deploy_obj.storage = LocalStorage(path="/opt/prefect/flow_code")
        deploy_obj.entrypoint = flow._entrypoint

        if docker_image not in docker_image_dict:
            docker_image_dict[docker_image] = {workpool_name: []}
        else:
            if workpool_name not in docker_image_dict[docker_image]:
                docker_image_dict[docker_image][workpool_name] = []

        docker_image_dict[docker_image][workpool_name].append(deploy_obj)

    for docker_image, workpool_names in docker_image_dict.items():
        try:
            for workpool_name, deploy_objs in workpool_names.items():
                kwargs = {
                    "build": False,
                    "push": False,
                    "image": docker_image,
                    "work_pool_name": workpool_name,
                }
                deployment_ids = deploy(*deploy_objs, **kwargs)
        except Exception as e:
            print(
                f"Failed to create deployments for docker image {docker_image} {str(e)}"
            )
            traceback.print_exc()
            continue
