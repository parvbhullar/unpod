from typing import Dict, List
from pydantic import BaseModel, Field


class CreateDocumentSchema(BaseModel):
    files: List[Dict]
    metadata: Dict = Field(default_factory=dict)
    schema: Dict
