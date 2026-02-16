from mongomantic import BaseRepository, MongoDBModel, Index
from services.messaging_service.core.mixin import CreateUpdateMixinModel
from services.task_service.schemas.deployment import DeploymentConfigSchema


class DeploymentConfigBaseModel(
    DeploymentConfigSchema, MongoDBModel, CreateUpdateMixinModel
):
    """MongoDB model for deployment configurations"""

    pass


class DeploymentConfigModel(BaseRepository):
    class Meta:
        model = DeploymentConfigBaseModel
        collection = "deployment_configs"
        indexes = [
            Index(fields=["name"], unique=True),  # Unique constraint for upsert
            Index(fields=["flow_name"]),  # Query by flow name
            Index(fields=["work_pool_name"]),  # Query by work pool
            Index(fields=["tags"]),  # Query by tags
        ]
