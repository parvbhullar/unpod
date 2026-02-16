from typing import Optional, List
from mongomantic import BaseRepository, MongoDBModel, Index
from pydantic import Field
from super_services.libs.core.mixin import CreateUpdateMixinModel


# =============================================================================
# Agent QA Pairs - Collection: agent_qa_pairs
# =============================================================================
class AgentQAPairBaseModel(MongoDBModel, CreateUpdateMixinModel):
    """Model for storing QA pairs generated from agent configuration."""

    agent_id: str = Field(...)
    question: str = Field(...)
    answer: str = Field(...)
    keywords: List[str] = Field(default_factory=list)
    status: str = Field(default="active")  # "active" or "inactive"
    batch_id: Optional[str] = Field(default=None)


class AgentQAPairModel(BaseRepository):
    class Meta:
        model = AgentQAPairBaseModel
        collection = "agent_qa_pairs"
        indexes = [
            Index(fields=["agent_id"]),
            Index(fields=["status"]),
            Index(fields=["batch_id"]),
        ]


# =============================================================================
# Knowledge Base QA Pairs - Collection: kb_qa_pairs
# =============================================================================
class KBQAPairBaseModel(MongoDBModel, CreateUpdateMixinModel):
    """Model for storing QA pairs generated from knowledge base documents."""

    agent_id: str = Field(...)
    kb_token: str = Field(...)
    question: str = Field(...)
    answer: str = Field(...)
    keywords: List[str] = Field(default_factory=list)
    status: str = Field(default="active")  # "active" or "inactive"
    batch_id: Optional[str] = Field(default=None)


class KBQAPairModel(BaseRepository):
    class Meta:
        model = KBQAPairBaseModel
        collection = "kb_qa_pairs"
        indexes = [
            Index(fields=["agent_id"]),
            Index(fields=["kb_token"]),
            Index(fields=["status"]),
            Index(fields=["batch_id"]),
        ]
