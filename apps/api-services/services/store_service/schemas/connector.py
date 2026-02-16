from typing import Any, Optional
from pydantic import BaseModel, Field


class ConnectorBase(BaseModel):
    name: str
    source: str
    input_type: str = "load_state"
    connector_specific_config: dict = Field(default_factory=dict)
    refresh_freq: Optional[int] = None
    prune_freq: Optional[int] = None
    disabled: bool = False


class ConnectorListResponse(ConnectorBase):
    id: str


class StatusResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None
