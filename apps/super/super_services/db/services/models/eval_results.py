from datetime import datetime
from typing import Dict, List, Optional
from mongomantic import BaseRepository, MongoDBModel, Index
from pydantic import Field

from super_services.libs.core.mixin import CreateUpdateMixinModel


class TestCaseResultModel(MongoDBModel):
    """Individual test case result."""
    test_case_index: int = Field(...)
    question: str = Field(...)
    expected_answer: str = Field(...)
    intent: str = Field(...)
    passed: bool = Field(...)
    actual_response: Optional[str] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    tool_called: Optional[str] = Field(default=None)
    expected_tool: Optional[str] = Field(default=None)


class EvalResultBaseModel(MongoDBModel, CreateUpdateMixinModel):
    """Evaluation results for an agent."""
    eval_id: str = Field(...)
    agent_id: str = Field(...)
    total_cases: int = Field(default=0)
    passed_cases: int = Field(default=0)
    failed_cases: int = Field(default=0)
    pass_rate: str = Field(default="0.0%")
    test_results: List[Dict] = Field(default_factory=list)
    eval_timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict = Field(default_factory=dict)


class EvalResultModel(BaseRepository):
    """Repository for evaluation results."""
    class Meta:
        model = EvalResultBaseModel
        collection = "eval_results"
        indexes = [
            Index(fields=["eval_id"]),
            Index(fields=["agent_id"]),
        ]