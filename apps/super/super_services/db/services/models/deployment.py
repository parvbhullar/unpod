from mongomantic import BaseRepository, MongoDBModel, Index
from super_services.db.services.schemas.deployment import DeploymentConfigSchema
from super_services.libs.core.mixin import CreateUpdateMixinModel


class DeploymentConfigBaseModel(DeploymentConfigSchema, MongoDBModel, CreateUpdateMixinModel):
    """MongoDB model for deployment configurations"""
    pass


class DeploymentConfigModel(BaseRepository):
    class Meta:
        model = DeploymentConfigBaseModel
        collection = "deployment_configs"
        indexes = [
            Index(fields=["name"], unique=True),  # Unique constraint for upsert
            Index(fields=["flow_name"]),          # Query by flow name
            Index(fields=["work_pool_name"]),     # Query by work pool
            Index(fields=["tags"]),               # Query by tags
        ]