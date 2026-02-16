from typing import Optional, Dict, List
from mongomantic import BaseRepository, MongoDBModel, Index
from pydantic import Field

from super_services.db.services.schemas.task import (
    CallRetrySmsSchema,
    UserBaseSchema,
    ArtifactSchema,
)
from super_services.libs.core.mixin import CreateUpdateMixinModel


class RunBaseModel(MongoDBModel, CreateUpdateMixinModel, UserBaseSchema):
    run_id: str = Field(...)
    batch_count: int = Field(default=0)
    collection_ref: str = Field(...)
    status: str = Field(default="pending")
    run_mode: str = Field(default="dev")
    call_analytics: Dict = Field(default_factory=dict)  # Call quality metrics
    execution_analytics: Dict = Field(default_factory=dict)  # Task execution metrics
    run_type: Optional[str] = Field(default=None)  # e.g., "call", "email"


class RunModel(BaseRepository):
    class Meta:
        model = RunBaseModel
        collection = "runs"
        indexes = [
            Index(fields=["run_id"]),
            Index(fields=["space_id"]),
            Index(fields=["run_mode"]),
            Index(fields=["user_org_id"]),
            Index(fields=["status"]),
            Index(fields=["thread_id"]),
            Index(fields=["run_type"]),
        ]


class TaskBaseModel(MongoDBModel, CreateUpdateMixinModel, UserBaseSchema):
    task_id: str = Field(...)
    run_id: str = Field(...)

    collection_ref: str = Field(...)
    task: Dict = Field(default_factory=dict)
    input: Dict = Field(default_factory=dict)
    output: Dict = Field(default_factory=dict)
    attachments: List[Dict] = Field(default_factory=list)
    assignee: str = Field(...)
    status: str = Field(default="pending")
    execution_type: Optional[str] = Field(default=None)
    ref_id: Optional[str] = Field(default=None)
    failure_count: int = Field(default=0)
    last_failure_reason: Optional[str] = Field(default=None)
    provider: Optional[str] = Field(default=None)  # Provider name (e.g., "vapi")
    retry_attempt: int = Field(default=0)  # Number of retry attempts made
    last_status_change: Optional[str] = Field(
        default=None
    )  # Timestamp of last status change
    scheduled_timestamp: Optional[int] = Field(
        default=None
    )  # Scheduled timestamp for future tasks


class TaskModel(BaseRepository):
    class Meta:
        model = TaskBaseModel
        collection = "tasks"
        # auto_create_index = False
        indexes = [
            Index(fields=["run_id"]),
            Index(fields=["space_id"]),
            Index(fields=["run_mode"]),
            Index(fields=["user_org_id"]),
            Index(fields=["status"]),
            Index(fields=["thread_id"]),
            Index(fields=["task_id"]),
            Index(fields=["execution_type"]),
            Index(fields=["ref_id"]),
            Index(fields=["scheduled_timestamp"]),
        ]


class TaskExecutionLogBaseModel(MongoDBModel, CreateUpdateMixinModel):
    task_exec_id: str = Field(...)
    task_id: str = Field(...)
    run_id: str = Field(...)
    executor_id: str = Field(...)
    status: str = Field(default="in_progress")
    input: Dict = Field(default_factory=dict)
    output: Dict = Field(default_factory=dict)
    data: Dict = Field(default_factory=dict)
    space_id: str = Field(...)


class TaskExecutionLogModel(BaseRepository):
    class Meta:
        model = TaskExecutionLogBaseModel
        collection = "task_execution_logs"
        indexes = [
            Index(fields=["task_exex_id"]),
            Index(fields=["task_id"]),
            Index(fields=["run_id"]),
            Index(fields=["status"]),
        ]


class ArtifactBaseModel(ArtifactSchema, MongoDBModel, CreateUpdateMixinModel):
    pass


class ArtifactModel(BaseRepository):
    class Meta:
        model = ArtifactBaseModel
        collection = "artifacts"
        indexes = [
            Index(fields=["fileId"]),
            Index(fields=["runId"]),
            Index(fields=["taskId"]),
            Index(fields=["threadId"]),
        ]


class CallRetrySmsBaseModel(CallRetrySmsSchema, MongoDBModel, CreateUpdateMixinModel):
    pass


class CallRetrySmsModel(BaseRepository):
    class Meta:
        model = CallRetrySmsBaseModel
        collection = "call_retry_sms"
        indexes = [
            Index(fields=["task_id"]),
            Index(fields=["contact_number"]),
            Index(fields=["temp_id"]),
            Index(fields=["status"]),
        ]
