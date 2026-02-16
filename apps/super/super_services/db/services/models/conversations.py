from mongomantic import BaseRepository, MongoDBModel, Index
from super_services.libs.core.mixin import CreateUpdateMixinModel

from super_services.db.services.schemas.conversation import (
    BlockModelSchema,
)


class BlockBaseModel(BlockModelSchema, MongoDBModel, CreateUpdateMixinModel):
    pass


class BlockModel(BaseRepository):
    class Meta:
        model = BlockBaseModel
        collection = "blocks"
        indexes = [
            Index(fields=["thread_id"]),
            Index(fields=["block_id"]),
            Index(fields=["user_id"]),
            Index(fields=["block_type"]),
            Index(fields=["block"]),
            Index(fields=["is_active"]),
        ]
