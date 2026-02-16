from mongomantic import BaseRepository, Index, MongoDBModel
from services.messaging_service.core.mixin import CreateUpdateMixinModel
from services.messaging_service.schemas.wallet import TaskRequest


class TaskRequestBaseModel(TaskRequest, MongoDBModel, CreateUpdateMixinModel):
    pass


class TaskRequestLogModel(BaseRepository):
    class Meta:
        model = TaskRequestBaseModel
        collection = "task_request_log"
        indexes = [
            Index(fields=["thread_id"]),
            Index(fields=["user_id"]),
            Index(fields=["org_id"]),
            Index(fields=["pilot"]),
            Index(fields=["status"]),
            Index(fields=["currency"]),
        ]
