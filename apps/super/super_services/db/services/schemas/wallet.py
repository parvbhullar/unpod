import decimal
import enum
from typing import Dict, Optional, Union
from pydantic import BaseModel, Field


class TaskRequestStatusEnum(enum.IntEnum):
    TASK_CREATED = 1
    HISTORY_DONE = 2


class TaskRequest(BaseModel):
    thread_id: Optional[Union[str, int]] = None
    user_id: Union[int, str]
    org_id: Union[int, str]
    pilot: str
    user: Dict = Field(default_factory=dict)
    tokens: Dict = Field(default_factory=dict)
    cost: decimal.Decimal = Field(default=decimal.Decimal(0), decimal_places=6)
    bits: decimal.Decimal = Field(default=decimal.Decimal(0), decimal_places=6)
    currency: str = Field(default="USD")
    metadata: Dict = Field(default_factory=dict)
    status: TaskRequestStatusEnum = Field(default=TaskRequestStatusEnum.TASK_CREATED)
    history_metadata: Dict = Field(default_factory=dict)

    class Config:
        json_encoders = {decimal.Decimal: str}
        json_schema_extra = {
            "example": {
                "thread_id": 1,
                "user_id": 1,
                "org_id": 1,
                "pilot": "test",
                "user": {},
                "tokens": {},
                "cost": decimal.Decimal(0),
                "bits": decimal.Decimal(0),
                "currency": "USD",
                "metadata": {},
            }
        }
