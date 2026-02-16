from typing import Dict, Union
from pydantic import BaseModel, Field
import time


class IndexJobSchema(BaseModel):
    org_id: Union[int, str]
    token: str
    file_path: str
    file_sha1: str
    schema: Dict = Field(default_factory=dict)
    upload: bool = False
    index: bool = False
    upload_at: int = Field(default_factory=lambda: int(time.time()))
    index_at: int = Field(default=0)
    retry: int = Field(default=0)
    error_log: dict = Field(default_factory=dict)
