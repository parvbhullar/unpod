from datetime import datetime, timezone
from pydantic import BaseModel, Field


def _utc_now():
    """Return current UTC time. Helper for Pydantic default_factory."""
    return datetime.now(timezone.utc)


class CreateUpdateMixinModel(BaseModel):
    created: datetime = Field(default_factory=_utc_now)
    modified: datetime = Field(default_factory=_utc_now)
