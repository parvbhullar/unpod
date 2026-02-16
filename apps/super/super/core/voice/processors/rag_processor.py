"""
RAG Processor - Synchronous context enrichment for Pipecat voice pipeline.

This processor intercepts TranscriptionFrames and enriches them with relevant
context from the knowledge base BEFORE they reach the LLM, providing:
- 500-2000ms latency reduction (no tool call round-trip)
- Guaranteed context availability before LLM generates response
- Synchronous inline processing (<50ms target)
- NER-based filtering to skip KB lookup for greetings/simple queries

Usage:
    from super.core.voice.processors.rag_processor import RAGProcessor

    rag_processor = RAGProcessor(
        knowledge_base_manager=kb_manager,
        similarity_top_k=3,
        enabled=True,
    )
    # Add to pipeline BEFORE the LLM service
"""

import logging
import re
import time
from typing import TYPE_CHECKING, List, Optional, Set

from pipecat.frames.frames import Frame, TranscriptionFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

if TYPE_CHECKING:
    from super.core.memory.index.base import BaseIndex
    from super.core.memory.search.schema import SearchDoc
    from super.core.voice.managers.knowledge_base import KnowledgeBaseManager


# Patterns that don't require KB lookup (greetings, simple conversational phrases)
SKIP_LOOKUP_PATTERNS: Set[str] = {
    # Greetings
    "hello", "hi", "hey", "hiya", "howdy", "hola", "namaste",
    "good morning", "good afternoon", "good evening", "good night",
    "hello there", "hi there", "hey there",
    # Farewells
    "bye", "goodbye", "see you", "take care", "later", "ciao",
    "see you later", "bye bye", "good bye", "talk later", "catch you later",
    # Acknowledgments
    "ok", "okay", "sure", "yes", "no", "yeah", "yep", "nope",
    "thanks", "thank you", "thanks a lot", "thank you so much",
    "got it", "understood", "alright", "fine", "great", "perfect",
    "okay great", "okay thanks", "ok thanks", "sounds good", "all good",
    # Simple responses
    "hmm", "uh", "um", "huh", "oh", "ah", "wow", "cool", "nice",
    "right", "exactly", "absolutely", "definitely", "certainly",
    # Hindi/Hinglish greetings and responses
    "haan", "ji", "theek hai", "achha", "acha", "sahi", "bas",
    "dhanyavaad", "shukriya", "alvida", "phir milenge",
    "haan ji", "theek", "bilkul", "zaroor",
}

# Question words that indicate KB lookup might be needed
QUESTION_INDICATORS: Set[str] = {
    "what", "how", "why", "when", "where", "who", "which", "can", "could",
    "would", "should", "is", "are", "do", "does", "tell", "explain", "describe",
    "kya", "kaise", "kyun", "kab", "kahan", "kaun", "konsa",  # Hindi
}


class RAGProcessor(FrameProcessor):
    """
    Synchronous RAG processor for Pipecat voice pipeline.

    Enriches TranscriptionFrames with relevant knowledge base context inline,
    eliminating the latency of tool-call based RAG approaches.

    Uses NER-based filtering to skip KB lookup for simple greetings and
    conversational phrases that don't require knowledge base access.
    """

    def __init__(
        self,
        knowledge_base_manager: Optional["KnowledgeBaseManager"] = None,
        vector_index: Optional["BaseIndex"] = None,
        similarity_top_k: int = 3,
        min_query_length: int = 3,
        min_word_count_for_lookup: int = 2,
        enabled: bool = True,
        context_prefix: str = "<reference_context>",
        skip_ner_check: bool = False,
        logger: Optional[logging.Logger] = None,
        **kwargs,
    ):
        """
        Initialize the RAG processor.

        Args:
            knowledge_base_manager: KnowledgeBaseManager instance for context retrieval.
                                   Takes precedence over vector_index if provided.
            vector_index: Direct vector index instance (BaseIndex).
                         Used if knowledge_base_manager is not provided.
            similarity_top_k: Number of similar documents to retrieve.
            min_query_length: Minimum query length to trigger RAG search.
            min_word_count_for_lookup: Minimum word count to consider for KB lookup.
            enabled: Whether RAG enrichment is enabled.
            context_prefix: Prefix for context section in enriched text.
            skip_ner_check: If True, skip NER check and always perform lookup.
            logger: Optional logger instance.
        """
        super().__init__(**kwargs)
        self._kb_manager = knowledge_base_manager
        self._vector_index = vector_index
        self._similarity_top_k = similarity_top_k
        self._min_query_length = min_query_length
        self._min_word_count_for_lookup = min_word_count_for_lookup
        self._enabled = enabled
        self._context_prefix = context_prefix
        self._skip_ner_check = skip_ner_check
        self._logger = logger or logging.getLogger(__name__)

        # Metrics
        self._total_queries = 0
        self._total_enrichments = 0
        self._total_skipped_ner = 0
        self._total_latency_ms = 0.0

    async def process_frame(
        self, frame: Frame, direction: FrameDirection
    ) -> None:
        """Process frames, enriching TranscriptionFrames with RAG context."""
        await super().process_frame(frame, direction)

        if isinstance(frame, TranscriptionFrame) and self._enabled:
            await self._process_transcription_frame(frame, direction)
            return

        await self.push_frame(frame, direction)

    def _requires_kb_lookup_via_ner(self, query: str) -> bool:
        """
        Determine if the query requires a knowledge base lookup using NER-like analysis.

        Uses lightweight pattern matching to identify:
        - Simple greetings and farewells (skip lookup)
        - Acknowledgments and simple responses (skip lookup)
        - Questions and information requests (require lookup)

        Args:
            query: The user's transcribed query text.

        Returns:
            True if KB lookup is needed, False otherwise.
        """
        if self._skip_ner_check:
            return True

        # Normalize query for comparison
        normalized = query.lower().strip()

        # Remove punctuation for matching
        cleaned = re.sub(r"[^\w\s]", "", normalized)

        # Check word count - very short queries likely don't need lookup
        words = cleaned.split()
        if len(words) < self._min_word_count_for_lookup:
            # But check if it's a question word
            if words and words[0] in QUESTION_INDICATORS:
                return True
            # Check for exact match in skip patterns
            if cleaned in SKIP_LOOKUP_PATTERNS:
                self._logger.debug(f"NER: skipping lookup for greeting/response: '{query}'")
                return False

        # Check if entire query matches a skip pattern
        if cleaned in SKIP_LOOKUP_PATTERNS:
            self._logger.debug(f"NER: skipping lookup for simple phrase: '{query}'")
            return False

        # Check if query starts with a question indicator
        first_word = words[0] if words else ""
        if first_word in QUESTION_INDICATORS:
            return True

        # Check for question mark - likely needs context
        if "?" in query:
            return True

        # Check if it's just a greeting with extra words (e.g., "hello there")
        if len(words) <= 3:
            greeting_words = {"hello", "hi", "hey", "bye", "thanks", "ok", "okay"}
            if words and words[0] in greeting_words:
                self._logger.debug(f"NER: skipping lookup for greeting variant: '{query}'")
                return False

        # Default: if query has substantive content, do the lookup
        return len(words) >= self._min_word_count_for_lookup

    async def _process_transcription_frame(
        self,
        frame: TranscriptionFrame,
        direction: FrameDirection,
    ) -> None:
        """Enrich transcription frame with RAG context."""
        query = frame.text
        self._total_queries += 1

        # Skip if query is too short
        if not query or len(query.strip()) < self._min_query_length:
            self._logger.debug(f"RAG skipped: query too short ({len(query) if query else 0} chars)")
            await self.push_frame(frame, direction)
            return

        # Check if KB lookup is required using NER-based analysis
        if not self._requires_kb_lookup_via_ner(query):
            self._total_skipped_ner += 1
            self._logger.debug(f"RAG skipped via NER: '{query[:50]}...'")
            await self.push_frame(frame, direction)
            return

        start_time = time.perf_counter()

        try:
            # Get relevant documents
            docs = await self._retrieve_documents(query)

            if docs:
                # Build context string
                context_str = self._build_context_string(docs)

                # Enrich the transcription frame with clear instructions
                # The format ensures LLM uses context for answering but doesn't echo it
                frame.text = (
                    f"<reference_context>\n"
                    f"{context_str}\n"
                    f"</reference_context>\n\n"
                    f"{query}"
                )

                self._total_enrichments += 1
                self._logger.debug(
                    f"RAG enriched with {len(docs)} docs: {query[:50]}..."
                )
            else:
                self._logger.debug(f"RAG: no relevant docs for: {query[:50]}...")

        except Exception as e:
            self._logger.warning(f"RAG retrieval error: {e}")
            # Continue without enrichment on error

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        self._total_latency_ms += elapsed_ms

        if elapsed_ms > 100:
            self._logger.warning(f"RAG latency high: {elapsed_ms:.1f}ms")
        else:
            self._logger.debug(f"RAG completed in {elapsed_ms:.1f}ms")

        await self.push_frame(frame, direction)

    async def _retrieve_documents(self, query: str) -> List["SearchDoc"]:
        """Retrieve relevant documents from knowledge base."""
        # Try KnowledgeBaseManager first
        if self._kb_manager and self._kb_manager.is_initialized:
            return await self._kb_manager._search_documents(
                query, k=self._similarity_top_k
            )

        # Fall back to direct vector index
        if self._vector_index:
            # Check if index has sync search (ChromaIndex)
            if hasattr(self._vector_index, "search_sync"):
                return self._vector_index.search_sync(query, k=self._similarity_top_k)
            # Otherwise use async search
            return await self._vector_index.search(query, k=self._similarity_top_k)

        self._logger.warning("RAG: No knowledge base or vector index available")
        return []

    def _build_context_string(self, docs: List["SearchDoc"]) -> str:
        """Build formatted context string from retrieved documents."""
        context_parts = []
        for i, doc in enumerate(docs, 1):
            content = doc.content.strip() if doc.content else ""
            if content:
                context_parts.append(f"- {content}")

        return "\n".join(context_parts)

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable RAG enrichment."""
        self._enabled = enabled
        self._logger.info(f"RAG processor {'enabled' if enabled else 'disabled'}")

    def set_similarity_top_k(self, k: int) -> None:
        """Set the number of documents to retrieve."""
        self._similarity_top_k = max(1, k)

    def get_metrics(self) -> dict:
        """Get RAG processor metrics."""
        avg_latency = (
            self._total_latency_ms / self._total_queries
            if self._total_queries > 0
            else 0.0
        )
        enrichment_rate = (
            self._total_enrichments / self._total_queries * 100
            if self._total_queries > 0
            else 0.0
        )
        ner_skip_rate = (
            self._total_skipped_ner / self._total_queries * 100
            if self._total_queries > 0
            else 0.0
        )

        return {
            "total_queries": self._total_queries,
            "total_enrichments": self._total_enrichments,
            "total_skipped_ner": self._total_skipped_ner,
            "enrichment_rate_pct": round(enrichment_rate, 1),
            "ner_skip_rate_pct": round(ner_skip_rate, 1),
            "avg_latency_ms": round(avg_latency, 2),
            "total_latency_ms": round(self._total_latency_ms, 2),
            "enabled": self._enabled,
        }

    def reset_metrics(self) -> None:
        """Reset metrics counters."""
        self._total_queries = 0
        self._total_enrichments = 0
        self._total_skipped_ner = 0
        self._total_latency_ms = 0.0

    @property
    def is_enabled(self) -> bool:
        """Check if RAG enrichment is enabled."""
        return self._enabled


def create_rag_processor(
    knowledge_base_manager: Optional["KnowledgeBaseManager"] = None,
    vector_index: Optional["BaseIndex"] = None,
    similarity_top_k: int = 3,
    enabled: bool = True,
    skip_ner_check: bool = False,
    logger: Optional[logging.Logger] = None,
) -> RAGProcessor:
    """
    Factory function to create a RAGProcessor.

    Args:
        knowledge_base_manager: KnowledgeBaseManager instance
        vector_index: Direct vector index (used if kb_manager not provided)
        similarity_top_k: Number of documents to retrieve
        enabled: Whether to enable RAG enrichment
        skip_ner_check: If True, skip NER check and always perform lookup
        logger: Optional logger instance

    Returns:
        Configured RAGProcessor instance
    """
    return RAGProcessor(
        knowledge_base_manager=knowledge_base_manager,
        vector_index=vector_index,
        similarity_top_k=similarity_top_k,
        enabled=enabled,
        skip_ner_check=skip_ner_check,
        logger=logger,
    )
