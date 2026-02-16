"""Tests for intent classification."""

import pytest

from super.core.orchestrator.three_layer.classifier import (
    IntentType,
    ClassificationResult,
    classify_intent,
)
from super.core.orchestrator.three_layer.models import ExecutionMode


class TestIntentType:
    """Tests for IntentType enum."""

    def test_all_intents_defined(self) -> None:
        intents = [i.value for i in IntentType]
        assert "greeting" in intents
        assert "simple_query" in intents
        assert "provider_search" in intents
        assert "booking" in intents
        assert "phone_call" in intents


class TestClassifyIntent:
    """Tests for classify_intent function."""

    @pytest.mark.parametrize("input_text,expected_intent,expected_mode", [
        ("Hello", IntentType.GREETING, ExecutionMode.SYNC),
        ("Hi there", IntentType.GREETING, ExecutionMode.SYNC),
        ("Good morning", IntentType.GREETING, ExecutionMode.SYNC),
        ("What's the weather?", IntentType.SIMPLE_QUERY, ExecutionMode.SYNC),
        ("Find me a dentist", IntentType.PROVIDER_SEARCH, ExecutionMode.ASYNC),
        ("Search for doctors nearby", IntentType.PROVIDER_SEARCH, ExecutionMode.ASYNC),
        ("Book an appointment", IntentType.BOOKING, ExecutionMode.ASYNC),
        ("Call Dr. Smith", IntentType.PHONE_CALL, ExecutionMode.ASYNC),
    ])
    def test_classify_intent(
        self,
        input_text: str,
        expected_intent: IntentType,
        expected_mode: ExecutionMode,
    ) -> None:
        result = classify_intent(input_text)
        assert result.intent == expected_intent
        assert result.mode == expected_mode

    def test_classification_result_has_confidence(self) -> None:
        result = classify_intent("Hello")
        assert 0.0 <= result.confidence <= 1.0

    def test_unknown_defaults_to_sync(self) -> None:
        result = classify_intent("asdfghjkl random gibberish")
        assert result.mode == ExecutionMode.SYNC
