from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum


class TaskStatusEnum(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    hold = "hold"
    failed = "failed"
    partially_completed = "partially_completed"
    processing = "processing"
    scheduled = "scheduled"


class UserBaseSchema(BaseModel):
    space_id: str = Field(...)
    thread_id: Optional[str] = Field(default=None)
    user: str = Field(...)
    user_org_id: Optional[str] = Field(default=None)
    user_info: dict = Field(default_factory=dict)


class RunModelSchema(BaseModel):
    run_id: str
    space_id: str
    batch_count: int = 0
    user: str
    collection_ref: str
    batch_units: int = 0
    status: TaskStatusEnum = Field(default=TaskStatusEnum.pending)
    run_mode: str = Field(default="Prod")
    thread_id: Optional[str] = Field(default=None)
    owner_org_id: Optional[str] = Field(default=None)
    user_org_id: Optional[str] = Field(default=None)
    user_id: Optional[str] = Field(default=None)
    call_analytics: Dict = Field(default_factory=dict)  # Call quality metrics
    execution_analytics: Dict = Field(default_factory=dict)  # Task execution metrics


class TaskModelSchema(BaseModel):
    task_id: str
    run_id: str
    thread_id: Optional[str] = Field(default=None)
    collection_ref: str
    task: Dict = Field(default_factory=dict)
    input: Dict = Field(default_factory=dict)
    output: Dict = Field(default_factory=dict)
    attachments: List[str] = Field(default_factory=list)
    assignee: str
    status: TaskStatusEnum = Field(default=TaskStatusEnum.pending)
    execution_units: int = Field(default=0)
    ref_id: Optional[str] = Field(default=None)
    owner_org_id: Optional[str] = Field(default=None)
    user_org_id: Optional[str] = Field(default=None)
    user_id: Optional[str] = Field(default=None)
    space_id: Optional[str] = Field(default=None)


class TaskExecutionLogSchema(BaseModel):
    task_exec_id: str
    task_id: str
    run_id: str
    executor_id: str
    status: TaskStatusEnum = Field(default=TaskStatusEnum.in_progress)
    input: Dict = Field(default_factory=dict)
    output: Dict = Field(default_factory=dict)
    data: Dict = Field(default_factory=dict)
    space_id: str
    owner_org_id: Optional[str] = Field(default=None)


class ArtifactSchema(BaseModel):
    file_id: str
    path: str
    thread_id: Optional[str] = Field(default=None)
    run_id: Optional[str] = Field(default=None)
    task_id: Optional[str] = Field(default=None)
    owner_org_id: Optional[str] = Field(default=None)
    space_id: str


class CallRetrySmsSchema(BaseModel):
    task_id: str
    contact_number: str
    temp_id: str
    kargs: Dict = Field(default_factory=dict)
    input_data: Dict = Field(default_factory=dict)
    status: TaskStatusEnum = Field(default=TaskStatusEnum.pending)
