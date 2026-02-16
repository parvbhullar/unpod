"""Intent classification for three-layer orchestration."""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple

from super.core.orchestrator.three_layer.models import ExecutionMode


class IntentType(Enum):
    """Types of user intents."""

    GREETING = "greeting"
    SIMPLE_QUERY = "simple_query"
    CLARIFICATION = "clarification"
    FOLLOWUP = "followup"
    PROVIDER_SEARCH = "provider_search"
    BOOKING = "booking"
    PHONE_CALL = "phone_call"
    RESEARCH = "research"
    UNKNOWN = "unknown"


@dataclass
class ClassificationResult:
    """Result of intent classification."""

    intent: IntentType
    mode: ExecutionMode
    confidence: float
    entities: Dict[str, str] = field(default_factory=dict)


SYNC_INTENTS = {
    IntentType.GREETING,
    IntentType.SIMPLE_QUERY,
    IntentType.CLARIFICATION,
    IntentType.FOLLOWUP,
    IntentType.UNKNOWN,
}

ASYNC_INTENTS = {
    IntentType.PROVIDER_SEARCH,
    IntentType.BOOKING,
    IntentType.PHONE_CALL,
    IntentType.RESEARCH,
}

PATTERNS: List[Tuple[str, IntentType]] = [
    (r"^(hi|hello|hey|good\s*(morning|afternoon|evening))", IntentType.GREETING),
    (r"(find|search|look\s*for).*(doctor|dentist|provider|specialist)", IntentType.PROVIDER_SEARCH),
    (r"(book|schedule|make).*(appointment|booking)", IntentType.BOOKING),
    (r"(call|phone|dial|ring)", IntentType.PHONE_CALL),
    (r"(what|how|when|where|why|which|who)", IntentType.SIMPLE_QUERY),
]


def classify_intent(input_text: str) -> ClassificationResult:
    """
    Classify user input into intent and execution mode.

    This is a simple pattern-based classifier. In production,
    use LLM-based classification for better accuracy.
    """
    text_lower = input_text.lower().strip()

    for pattern, intent in PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            mode = ExecutionMode.ASYNC if intent in ASYNC_INTENTS else ExecutionMode.SYNC
            return ClassificationResult(
                intent=intent,
                mode=mode,
                confidence=0.8,
                entities={},
            )

    return ClassificationResult(
        intent=IntentType.UNKNOWN,
        mode=ExecutionMode.SYNC,
        confidence=0.3,
        entities={},
    )
