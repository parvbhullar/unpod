from typing import Optional, List
from mongomantic import BaseRepository, MongoDBModel, Index
from pydantic import Field
from super_services.libs.core.mixin import CreateUpdateMixinModel


# =============================================================================
# Agent QA Pairs - Collection: agent_qa_pairs
# =============================================================================
class AgentQAPairBaseModel(MongoDBModel, CreateUpdateMixinModel):
    """Model for storing QA pairs generated from agent configuration."""

    question: str = Field(...)
    answer: str = Field(...)
    keywords: List[str] = Field(default_factory=list)
    eval_type: Optional[str] = Field(default=None)
    intent: Optional[str] = Field(default=None)
    is_first_message: bool = Field(default=False)
    is_tool_call: bool = Field(default=False)
    tool_name: Optional[str] = Field(default=None)
    source: Optional[str] = Field(default=None)
    language: Optional[str] = Field(default=None)
    status: str = Field(default="active")  # "active" or "inactive"
    batch_id: Optional[str] = Field(default=None)


class AgentQAPairModel(BaseRepository):
    class Meta:
        model = AgentQAPairBaseModel
        collection = "agent_qa_pairs"
        indexes = [
            Index(fields=["status"]),
            Index(fields=["batch_id"]),
            Index(fields=["eval_type"]),
        ]

    def __init__(self, token):
        self.Meta.collection = f"collection_data_{token}"


# =============================================================================
# Knowledge Base QA Pairs - Collection: kb_qa_pairs
# =============================================================================
class KBQAPairBaseModel(MongoDBModel, CreateUpdateMixinModel):
    """Model for storing QA pairs generated from knowledge base documents."""

    question: str = Field(...)
    answer: str = Field(...)
    keywords: List[str] = Field(default_factory=list)
    eval_type: Optional[str] = Field(default=None)
    intent: Optional[str] = Field(default=None)
    is_first_message: bool = Field(default=False)
    is_tool_call: bool = Field(default=False)
    tool_name: Optional[str] = Field(default=None)
    source: Optional[str] = Field(default=None)
    language: Optional[str] = Field(default=None)
    status: str = Field(default="active")  # "active" or "inactive"
    batch_id: Optional[str] = Field(default=None)


class KBQAPairModel(BaseRepository):
    class Meta:
        model = KBQAPairBaseModel
        collection = "kb_qa_pairs"
        indexes = [
            Index(fields=["status"]),
            Index(fields=["batch_id"]),
            Index(fields=["eval_type"]),
        ]

    def __init__(self, token):
        self.Meta.collection = f"collection_data_{token}"
