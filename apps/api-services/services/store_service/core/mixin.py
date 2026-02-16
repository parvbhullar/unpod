from datetime import datetime, timezone
from pydantic import BaseModel, Field


def get_utc_now():
    return datetime.now(timezone.utc)


class CreateUpdateMixinModel(BaseModel):
    created: datetime = Field(default_factory=get_utc_now)
    modified: datetime = Field(default_factory=get_utc_now)
