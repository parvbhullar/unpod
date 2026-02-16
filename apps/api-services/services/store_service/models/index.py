from typing import Any, Optional
from mongomantic import BaseRepository, MongoDBModel, Index

from services.store_service.core.mixin import CreateUpdateMixinModel
from services.store_service.schemas.index import IndexJobSchema


class IndexJobBaseModel(IndexJobSchema, MongoDBModel, CreateUpdateMixinModel):
    id: Optional[Any] = None


class IndexJobModel(BaseRepository):
    class Meta:
        model = IndexJobBaseModel
        collection = "index_jobs"
        indexes = [
            Index(fields=["org_id"]),
            Index(fields=["token"]),
            Index(fields=["index"]),
            Index(fields=["upload"]),
            Index(fields=["file_sha1"]),
        ]
