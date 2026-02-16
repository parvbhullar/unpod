from typing import Dict
from mongomantic import BaseRepository, MongoDBModel, Index
from pydantic import Field


class ClassificationBaseModel(MongoDBModel):
    token: str = Field(...)
    document_id: str = Field(...)
    status: str = Field(default="incomplete")
    data: Dict = Field(default_factory=dict)


class ClassificationModel(BaseRepository):
    class Meta:
        model = ClassificationBaseModel
        collection = "classifications"
        indexes = [
            Index(fields=["document_id"]),
            Index(fields=["token"]),
            Index(fields=["status"]),
        ]
