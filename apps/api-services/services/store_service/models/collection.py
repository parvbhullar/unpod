from typing import Any, Optional
from mongomantic import BaseRepository, MongoDBModel, Index

from services.store_service.core.mixin import CreateUpdateMixinModel
from services.store_service.schemas.collection import (
    CollectionFileLogSchema,
    CollectionModelConfig,
    CollectionModelSchema,
)


class CollectionConfigBaseModel(
    CollectionModelConfig, MongoDBModel, CreateUpdateMixinModel
):
    id: Optional[Any] = None


class CollectionConfigModel(BaseRepository):
    class Meta:
        model = CollectionConfigBaseModel
        collection = "collection_config"
        indexes = [
            Index(fields=["org_id"]),
            Index(fields=["token"]),
            Index(fields=["collection_type"]),
        ]


class CollectionSchemaBaseModel(
    CollectionModelSchema, MongoDBModel, CreateUpdateMixinModel
):
    id: Optional[Any] = None


class CollectionSchemaModel(BaseRepository):
    class Meta:
        model = CollectionSchemaBaseModel
        collection = "collection_schema"
        indexes = [
            Index(fields=["org_id"]),
            Index(fields=["token"]),
            Index(fields=["collection_id"]),
        ]


class CollectionFileLogBaseModel(
    CollectionFileLogSchema, MongoDBModel, CreateUpdateMixinModel
):
    id: Optional[Any] = None


class CollectionFileLogModel(BaseRepository):
    class Meta:
        model = CollectionFileLogBaseModel
        collection = "collection_file_log"
        indexes = [
            Index(fields=["collection_id"]),
        ]
