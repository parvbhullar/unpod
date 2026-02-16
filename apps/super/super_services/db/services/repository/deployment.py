from typing import Dict, List, Optional
from super_services.db.services.models.deployment import DeploymentConfigModel
from super_services.libs.core.datetime import get_datetime_now
from super_services.libs.core.jsondecoder import convert_decimal


def upsert_deployment_config(deployment_data: Dict) -> Dict:
    """
    Insert or update deployment configuration based on name.

    Args:
        deployment_data: Dict with keys: name, flow_name, docker_image, work_pool_name, tags, concurrency

    Returns:
        Dict: The saved deployment config document
    """
    name = deployment_data.get("name")
    if not name:
        raise ValueError("Deployment name is required")

    # Check if deployment exists
    existing = DeploymentConfigModel.find_one(name=name)

    if existing:
        # UPDATE path
        update_data = {
            "flow_name": deployment_data.get("flow_name", ""),
            "docker_image": deployment_data.get("docker_image"),
            "work_pool_name": deployment_data.get("work_pool_name"),
            "tags": deployment_data.get("tags", []),
            "concurrency": deployment_data.get("concurrency", 10),
            "modified": get_datetime_now(utc=True),
        }
        DeploymentConfigModel.update_one({"name": name}, update_data)
        result = DeploymentConfigModel.find_one(name=name)
    else:
        # INSERT path
        create_data = {
            "name": name,
            "flow_name": deployment_data.get("flow_name", ""),
            "docker_image": deployment_data.get("docker_image"),
            "work_pool_name": deployment_data.get("work_pool_name"),
            "tags": deployment_data.get("tags", []),
            "concurrency": deployment_data.get("concurrency", 10),
            "created": get_datetime_now(utc=True),
            "modified": get_datetime_now(utc=True),
        }

        # Create model instance and convert to MongoDB format
        model_instance = DeploymentConfigModel.Meta.model(**create_data)
        mongo_data = convert_decimal(model_instance.to_mongo())

        # Insert into MongoDB
        insert_result = DeploymentConfigModel._get_collection().insert_one(mongo_data)
        result = DeploymentConfigModel.find_one(name=name)

    return result


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


def delete_deployment_config(name: str) -> bool:
    """Delete deployment config by name"""
    result = DeploymentConfigModel.delete_many(name=name)
    return result.deleted_count > 0


def bulk_upsert_deployment_configs(deployment_list: List[Dict]) -> List[Dict]:
    """
    Bulk upsert multiple deployment configurations.

    Args:
        deployment_list: List of deployment config dicts

    Returns:
        List of saved deployment config dicts
    """
    results = []
    for deployment_data in deployment_list:
        try:
            result = upsert_deployment_config(deployment_data)
            results.append(result)
        except Exception as e:
            print(f"Error upserting deployment {deployment_data.get('name')}: {e}")
            continue

    return results


def sync_deployment_configs_to_db(deployment_configurations: List[Dict]) -> List[Dict]:
    """
    Extract and sync deployment configurations to MongoDB.
    This is called automatically during deployment creation.

    Args:
        deployment_configurations: List of deployment config dicts (from DEPLOYMENT_CONFIGURATIONS)

    Returns:
        List of saved deployment config dicts
    """
    configs_to_save = []

    for deployment in deployment_configurations:
        # Extract flow name from flow object
        flow = deployment.get("flow")
        flow_name = flow.name if flow and hasattr(flow, "name") else ""

        # Extract only non-sensitive, serializable fields
        config_data = {
            "name": deployment["name"],
            "flow_name": flow_name,
            "docker_image": deployment.get("docker_image", ""),
            "work_pool_name": deployment.get("work_pool_name", ""),
            "tags": deployment.get("tags", []),
            "concurrency": deployment.get("concurrency", 10),
        }
        configs_to_save.append(config_data)

    # Bulk upsert to MongoDB
    results = bulk_upsert_deployment_configs(configs_to_save)
    print(f"✓ Synced {len(results)} deployment configurations to MongoDB")
    return results
