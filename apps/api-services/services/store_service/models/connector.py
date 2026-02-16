from typing import Any, Optional
from mongomantic import BaseRepository, MongoDBModel, Index

from services.store_service.core.mixin import CreateUpdateMixinModel


class ConnectorBaseModel(MongoDBModel, CreateUpdateMixinModel):
    id: Optional[Any] = None
    name: str
    source: str
    input_type: str = "load_state"
    connector_specific_config: dict = {}
    refresh_freq: Optional[int] = None
    prune_freq: Optional[int] = None
    disabled: bool = False


class ConnectorModel(BaseRepository):
    class Meta:
        model = ConnectorBaseModel
        collection = "connectors"
        indexes = [
            Index(fields=["name"]),
            Index(fields=["source"]),
        ]
