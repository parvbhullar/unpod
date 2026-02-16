from datetime import datetime
from pydantic import BaseModel, Field


class CreateUpdateMixinModel(BaseModel):
    created: datetime = Field(default_factory=datetime.utcnow)
    modified: datetime = Field(default_factory=datetime.utcnow)
