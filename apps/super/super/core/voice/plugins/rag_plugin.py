"""
RAG Plugin - Knowledge base context enrichment for voice pipeline.

Wraps the RAGProcessor to integrate with the plugin system.
"""

import logging
from typing import TYPE_CHECKING, List, Optional

from super.core.voice.plugins.base import PipelinePlugin, PluginConfig, PluginPriority

if TYPE_CHECKING:
    from super.core.voice.pipecat.lite_handler import LiteVoiceHandler
    from super.core.voice.processors.rag_processor import RAGProcessor


class RAGPlugin(PipelinePlugin):
    """
    RAG plugin for knowledge base context enrichment.

    Adds RAGProcessor to the pipeline at PRE_LLM priority to enrich
    transcriptions with relevant context before LLM processing.

    Config options:
        similarity_top_k: Number of documents to retrieve (default: 3)
        kb_timeout: Timeout for KB initialization (default: 5.0)
        skip_ner_check: Skip NER filtering (default: False)
    """

    name = "rag"
    priority = PluginPriority.PRE_LLM

    def __init__(
        self,
        config: Optional[PluginConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        super().__init__(config, logger)
        self._processor: Optional["RAGProcessor"] = None
        self._kb_manager = None

    async def initialize(self, handler: "LiteVoiceHandler") -> None:
        """Initialize RAG plugin with handler's KB manager."""
        await super().initialize(handler)

        # Get config options
        similarity_top_k = self.options.get("similarity_top_k", 3)
        skip_ner_check = self.options.get("skip_ner_check", False)

        # Check if handler has KB manager initialized
        kb_manager = getattr(handler, "_kb_manager", None)

        # Create RAG processor
        from super.core.voice.processors.rag_processor import RAGProcessor

        self._processor = RAGProcessor(
            knowledge_base_manager=kb_manager,
            similarity_top_k=similarity_top_k,
            skip_ner_check=skip_ner_check,
            enabled=self._config.enabled,
            logger=self._logger,
        )

        self._logger.info(
            f"RAGPlugin initialized (top_k={similarity_top_k}, "
            f"skip_ner={skip_ner_check})"
        )

    def get_processors(self) -> List:
        """Return RAG processor for pipeline insertion."""
        if self._processor and self._config.enabled:
            return [self._processor]
        return []

    async def on_call_start(self) -> None:
        """Reset metrics on call start."""
        if self._processor:
            self._processor.reset_metrics()

    def get_metrics(self) -> Optional[dict]:
        """Get RAG processor metrics."""
        if self._processor:
            return self._processor.get_metrics()
        return None

    async def cleanup(self) -> None:
        """Clean up RAG plugin resources."""
        self._processor = None
        self._kb_manager = None
        await super().cleanup()

    def set_kb_manager(self, kb_manager) -> None:
        """Set KB manager after initialization (for late binding)."""
        self._kb_manager = kb_manager
        if self._processor:
            self._processor._kb_manager = kb_manager
            self._logger.info("KB manager set for RAG plugin")
