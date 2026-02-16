import traceback
from prefect import deploy
from prefect.runner.storage import LocalStorage

from super_services.db.services.repository.deployment import (
    sync_deployment_configs_to_db,
)


def create_deployment(deployment_confs):
    try:
        sync_deployment_configs_to_db(deployment_confs)
    except Exception as e:
        print("Failed to sync deployment configs to DB")
        traceback.print_exc()
        return
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
