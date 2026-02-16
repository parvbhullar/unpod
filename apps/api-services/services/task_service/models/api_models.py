from datetime import datetime
import enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from services.task_service.schemas.task import UserBaseSchema


class RunMode(str, enum.Enum):
    prod = "prod"
    test = "test"
    dev = "dev"
    prefect = "prefect"
    default = "default"


class TaskInput(BaseModel):
    message: dict


class TaskOutput(BaseModel):
    response: str


class Task(BaseModel):
    objective: str
    input_data: dict
    attachments: List[str]
    ref_id: Optional[str] = None
    execution_type: str


class APIRequestModel(BaseModel):
    space_id: str
    user: dict = Field(default_factory=dict)
    data: dict = Field(default_factory=dict)
    attachments: Optional[List[dict]] = []
    collection_ref: str
    run_mode: RunMode = Field(default=RunMode.dev)
    org_id: Optional[str] = None
    thread_id: Optional[str] = None
    assignee: str
    tasks: List[Task]

    @field_validator("space_id", mode="after")
    @classmethod
    def check_space(cls, value: str):
        if value and value.isalnum() and len(value) == 24:
            from services.messaging_service.core.wallet import fetchSpaceByToken

            space = fetchSpaceByToken(value)
            if space:
                return str(space["id"])
            raise ValueError("Invalid Space Token")
        return value


class APIResponseModel(BaseModel):
    run_id: str
    task_ids: List[str]
    status: dict


class RunsListModel(BaseModel):
    space_id: str
    user: str
    thread_id: Optional[str] = None
    run_id: str
    collection_ref: str
    run_mode: RunMode = Field(default=RunMode.dev)
    status: str
    batch_count: int
    created: datetime
    modified: datetime


class TaskListModel(UserBaseSchema):
    run_id: str
    task_id: str
    collection_ref: str
    execution_type: str
    task: Optional[Dict] = Field(default_factory=dict)
    input: Optional[Dict] = Field(default_factory=dict)
    output: Optional[Dict] = Field(default_factory=dict)
    attachments: Optional[List[dict]] = []
    ref_id: Optional[str] = None
    assignee: str

    run_mode: RunMode = Field(default=RunMode.dev)
    status: str
    created: datetime
    modified: datetime
