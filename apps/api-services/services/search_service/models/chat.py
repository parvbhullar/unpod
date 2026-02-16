from typing import Any, Optional
from mongomantic import BaseRepository, MongoDBModel, Index

from services.store_service.core.mixin import CreateUpdateMixinModel


class ChatSessionBaseModel(MongoDBModel, CreateUpdateMixinModel):
    id: Optional[Any] = None
    thread_id: str
    user_id: Optional[str] = None
    description: str = ""
    messages: list = []


class ChatSessionModel(BaseRepository):
    class Meta:
        model = ChatSessionBaseModel
        collection = "chat_sessions"
        indexes = [
            Index(fields=["thread_id"]),
            Index(fields=["user_id"]),
        ]
