from typing import Any, Optional
from mongomantic import BaseRepository, MongoDBModel, Index

from services.store_service.core.mixin import CreateUpdateMixinModel


class LLMProviderBaseModel(MongoDBModel, CreateUpdateMixinModel):
    id: Optional[Any] = None
    provider: str
    model_name: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    api_version: Optional[str] = None
    is_default: bool = False
    custom_config: dict = {}


class LLMProviderModel(BaseRepository):
    class Meta:
        model = LLMProviderBaseModel
        collection = "llm_providers"
        indexes = [
            Index(fields=["provider"]),
            Index(fields=["is_default"]),
        ]
