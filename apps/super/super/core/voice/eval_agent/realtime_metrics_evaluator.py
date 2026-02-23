"""
Realtime Metrics Evaluator using RAGAS and DeepEval.

Provides faithfulness, answer relevancy, hallucination detection,
G-Eval, factual consistency, and bias scoring for voice agent responses.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from super.core.logging import logging

logger = logging.get_logger(__name__)

# Track availability of evaluation libraries
_RAGAS_AVAILABLE: bool = False
_DEEPEVAL_AVAILABLE: bool = False


def _check_ragas_available() -> bool:
    """Check if RAGAS is available for import."""
    global _RAGAS_AVAILABLE
    try:
        from ragas.metrics import faithfulness, answer_relevancy
        from ragas import evaluate

        _RAGAS_AVAILABLE = True
    except ImportError:
        _RAGAS_AVAILABLE = False
    return _RAGAS_AVAILABLE


def _check_deepeval_available() -> bool:
    """Check if DeepEval is available for import."""
    global _DEEPEVAL_AVAILABLE
    try:
        from deepeval.metrics import GEval, FaithfulnessMetric, BiasMetric

        _DEEPEVAL_AVAILABLE = True
    except ImportError:
        _DEEPEVAL_AVAILABLE = False
    return _DEEPEVAL_AVAILABLE


# Check availability on module load
_check_ragas_available()
_check_deepeval_available()


@dataclass
class RagasMetrics:
    """RAGAS evaluation metrics."""

    faithfulness_score: float = 0.0
    answer_relevancy_score: float = 0.0
    hallucination_score: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "faithfulness_score": round(self.faithfulness_score, 4),
            "answer_relevancy_score": round(self.answer_relevancy_score, 4),
            "hallucination_score": round(self.hallucination_score, 4),
        }


@dataclass
class DeepEvalMetrics:
    """DeepEval evaluation metrics."""

    g_eval_score: float = 0.0
    factual_consistency_score: float = 0.0
    bias_score: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "g_eval_score": round(self.g_eval_score, 4),
            "factual_consistency_score": round(self.factual_consistency_score, 4),
            "bias_score": round(self.bias_score, 4),
        }


@dataclass
class CombinedMetrics:
    """Combined RAGAS and DeepEval metrics for a single turn."""

    ragas: RagasMetrics = field(default_factory=RagasMetrics)
    deepeval: DeepEvalMetrics = field(default_factory=DeepEvalMetrics)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ragas_metrics": self.ragas.to_dict(),
            "deepeval_metrics": self.deepeval.to_dict(),
        }


class RealtimeMetricsEvaluator:
    """
    Evaluator that computes RAGAS and DeepEval metrics for voice agent responses.

    Supports:
    - RAGAS: faithfulness, answer_relevancy, hallucination detection
    - DeepEval: G-Eval, factual consistency, bias detection
    """

    def __init__(
        self,
        model_config: Optional[Dict[str, Any]] = None,
        enable_ragas: bool = True,
        enable_deepeval: bool = True,
    ):
        """
        Initialize the metrics evaluator.

        Args:
            model_config: Configuration dict with eval settings.
            enable_ragas: Whether to compute RAGAS metrics.
            enable_deepeval: Whether to compute DeepEval metrics.
        """
        self.config = model_config or {}
        self.enable_ragas = enable_ragas and _RAGAS_AVAILABLE
        self.enable_deepeval = enable_deepeval and _DEEPEVAL_AVAILABLE

        if enable_ragas and not _RAGAS_AVAILABLE:
            logger.warning(
                "RAGAS requested but not available. Install with: pip install ragas"
            )
        if enable_deepeval and not _DEEPEVAL_AVAILABLE:
            logger.warning(
                "DeepEval requested but not available. Install with: pip install deepeval"
            )

        # LLM for evaluation (use configured or default)
        self._llm = None
        self._embeddings = None

    def _get_llm(self):
        """Get or create LLM for evaluation."""
        if self._llm is not None:
            return self._llm

        try:
            from langchain_openai import ChatOpenAI

            model_name = self.config.get("eval_llm_model", "gpt-4o-mini")
            self._llm = ChatOpenAI(model=model_name, temperature=0.0)
            return self._llm
        except ImportError:
            logger.warning("langchain_openai not available for RAGAS evaluation")
            return None

    def _get_embeddings(self):
        """Get or create embeddings model for evaluation."""
        if self._embeddings is not None:
            return self._embeddings

        try:
            from langchain_openai import OpenAIEmbeddings

            self._embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            return self._embeddings
        except ImportError:
            logger.warning("langchain_openai not available for embeddings")
            return None

    async def evaluate_ragas(
        self,
        question: str,
        answer: str,
        contexts: Optional[List[str]] = None,
        ground_truth: Optional[str] = None,
    ) -> RagasMetrics:
        """
        Compute RAGAS metrics for a single Q&A pair.

        Args:
            question: The user's question.
            answer: The agent's response.
            contexts: Retrieved context documents (for RAG evaluation).
            ground_truth: Expected answer for comparison.

        Returns:
            RagasMetrics with faithfulness, relevancy, and hallucination scores.
        """
        if not self.enable_ragas:
            return RagasMetrics(error="RAGAS not enabled or available")

        if not question or not answer:
            return RagasMetrics(error="Question or answer is empty")

        try:
            from ragas import evaluate, RunConfig
            from ragas.metrics import faithfulness, answer_relevancy
            from ragas.dataset_schema import SingleTurnSample, EvaluationDataset

            # Prepare contexts - use ground_truth as context if no contexts provided
            eval_contexts = (
                contexts if contexts else ([ground_truth] if ground_truth else [answer])
            )

            # Create sample for evaluation
            sample = SingleTurnSample(
                user_input=question,
                response=answer,
                retrieved_contexts=eval_contexts,
                reference=ground_truth or answer,
            )

            dataset = EvaluationDataset(samples=[sample])

            # Configure metrics
            metrics_to_use = [faithfulness, answer_relevancy]

            # Run evaluation
            llm = self._get_llm()
            embeddings = self._get_embeddings()

            run_config = RunConfig(max_workers=1, timeout=30)

            result = evaluate(
                dataset=dataset,
                metrics=metrics_to_use,
                llm=llm,
                embeddings=embeddings,
                run_config=run_config,
            )

            # Extract scores from result
            scores = result.to_pandas().iloc[0].to_dict() if len(result) > 0 else {}

            faithfulness_score = float(scores.get("faithfulness", 0.0) or 0.0)
            relevancy_score = float(scores.get("answer_relevancy", 0.0) or 0.0)

            # Calculate hallucination as inverse of faithfulness
            hallucination_score = 1.0 - faithfulness_score

            return RagasMetrics(
                faithfulness_score=faithfulness_score,
                answer_relevancy_score=relevancy_score,
                hallucination_score=hallucination_score,
            )

        except Exception as e:
            logger.error(f"RAGAS evaluation failed: {e}")
            return RagasMetrics(error=str(e))

    async def evaluate_deepeval(
        self,
        question: str,
        answer: str,
        context: Optional[str] = None,
        expected_output: Optional[str] = None,
    ) -> DeepEvalMetrics:
        """
        Compute DeepEval metrics for a single Q&A pair.

        Args:
            question: The user's question.
            answer: The agent's response.
            context: Context or knowledge base content.
            expected_output: Expected answer for comparison.

        Returns:
            DeepEvalMetrics with G-Eval, factual consistency, and bias scores.
        """
        if not self.enable_deepeval:
            return DeepEvalMetrics(error="DeepEval not enabled or available")

        if not question or not answer:
            return DeepEvalMetrics(error="Question or answer is empty")

        try:
            from deepeval.test_case import LLMTestCase
            from deepeval.metrics import GEval, FaithfulnessMetric, BiasMetric
            from deepeval.metrics.g_eval import GEvalTaskType

            # Create test case
            test_case = LLMTestCase(
                input=question,
                actual_output=answer,
                expected_output=expected_output or "",
                retrieval_context=[context] if context else None,
            )

            g_eval_score = 0.0
            factual_score = 0.0
            bias_score = 0.0

            # G-Eval for overall quality
            try:
                g_eval = GEval(
                    name="Coherence",
                    criteria="Determine if the response is coherent and well-structured.",
                    evaluation_params=[
                        "coherence",
                        "fluency",
                    ],
                    threshold=0.5,
                )
                await asyncio.to_thread(g_eval.measure, test_case)
                g_eval_score = float(g_eval.score or 0.0)
            except Exception as e:
                logger.warning(f"G-Eval failed: {e}")

            # Faithfulness/Factual Consistency
            if context:
                try:
                    faithfulness = FaithfulnessMetric(threshold=0.5)
                    await asyncio.to_thread(faithfulness.measure, test_case)
                    factual_score = float(faithfulness.score or 0.0)
                except Exception as e:
                    logger.warning(f"FaithfulnessMetric failed: {e}")

            # Bias detection
            try:
                bias = BiasMetric(threshold=0.5)
                await asyncio.to_thread(bias.measure, test_case)
                # Bias score is inverted (lower is better, so 1-score = how unbiased)
                bias_score = 1.0 - float(bias.score or 0.0)
            except Exception as e:
                logger.warning(f"BiasMetric failed: {e}")

            return DeepEvalMetrics(
                g_eval_score=g_eval_score,
                factual_consistency_score=factual_score,
                bias_score=bias_score,
            )

        except Exception as e:
            logger.error(f"DeepEval evaluation failed: {e}")
            return DeepEvalMetrics(error=str(e))

    async def evaluate_turn(
        self,
        question: str,
        answer: str,
        contexts: Optional[List[str]] = None,
        expected_output: Optional[str] = None,
    ) -> CombinedMetrics:
        """
        Evaluate a single conversation turn with both RAGAS and DeepEval.

        Args:
            question: The user's question.
            answer: The agent's response.
            contexts: Retrieved context documents.
            expected_output: Expected answer for comparison.

        Returns:
            CombinedMetrics with both RAGAS and DeepEval scores.
        """
        # Run RAGAS and DeepEval in parallel
        ragas_task = self.evaluate_ragas(
            question=question,
            answer=answer,
            contexts=contexts,
            ground_truth=expected_output,
        )

        deepeval_task = self.evaluate_deepeval(
            question=question,
            answer=answer,
            context=contexts[0] if contexts else expected_output,
            expected_output=expected_output,
        )

        ragas_result, deepeval_result = await asyncio.gather(
            ragas_task,
            deepeval_task,
            return_exceptions=True,
        )

        # Handle exceptions
        if isinstance(ragas_result, Exception):
            logger.error(f"RAGAS evaluation exception: {ragas_result}")
            ragas_result = RagasMetrics(error=str(ragas_result))

        if isinstance(deepeval_result, Exception):
            logger.error(f"DeepEval evaluation exception: {deepeval_result}")
            deepeval_result = DeepEvalMetrics(error=str(deepeval_result))

        return CombinedMetrics(ragas=ragas_result, deepeval=deepeval_result)

    async def evaluate_batch(
        self,
        turns: List[Dict[str, Any]],
        max_concurrent: int = 3,
    ) -> List[CombinedMetrics]:
        """
        Evaluate multiple conversation turns in batch.

        Args:
            turns: List of turn dicts with 'question', 'answer', 'contexts', 'expected_output'.
            max_concurrent: Maximum concurrent evaluations.

        Returns:
            List of CombinedMetrics for each turn.
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def evaluate_with_limit(turn: Dict[str, Any]) -> CombinedMetrics:
            async with semaphore:
                return await self.evaluate_turn(
                    question=turn.get("question", ""),
                    answer=turn.get("answer", ""),
                    contexts=turn.get("contexts"),
                    expected_output=turn.get("expected_output"),
                )

        results = await asyncio.gather(
            *[evaluate_with_limit(turn) for turn in turns],
            return_exceptions=True,
        )

        # Convert exceptions to empty metrics
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch evaluation failed for turn {i}: {result}")
                processed_results.append(CombinedMetrics())
            else:
                processed_results.append(result)

        return processed_results


# Singleton instance for reuse
_evaluator_instance: Optional[RealtimeMetricsEvaluator] = None


def get_realtime_metrics_evaluator(
    model_config: Optional[Dict[str, Any]] = None,
    enable_ragas: bool = True,
    enable_deepeval: bool = True,
) -> RealtimeMetricsEvaluator:
    """
    Get or create a singleton RealtimeMetricsEvaluator instance.

    Args:
        model_config: Configuration dict.
        enable_ragas: Whether to enable RAGAS metrics.
        enable_deepeval: Whether to enable DeepEval metrics.

    Returns:
        RealtimeMetricsEvaluator instance.
    """
    global _evaluator_instance
    if _evaluator_instance is None:
        _evaluator_instance = RealtimeMetricsEvaluator(
            model_config=model_config,
            enable_ragas=enable_ragas,
            enable_deepeval=enable_deepeval,
        )
    return _evaluator_instance


def is_ragas_available() -> bool:
    """Check if RAGAS is available."""
    return _RAGAS_AVAILABLE


def is_deepeval_available() -> bool:
    """Check if DeepEval is available."""
    return _DEEPEVAL_AVAILABLE
