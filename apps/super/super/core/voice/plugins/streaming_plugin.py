"""
Streaming Parser Plugin - Enables streaming TTS synthesis.

Wraps StreamingTextParserProcessor to integrate with the plugin system.
"""

import logging
from typing import TYPE_CHECKING, List, Optional

from super.core.voice.plugins.base import PipelinePlugin, PluginConfig, PluginPriority

if TYPE_CHECKING:
    from super.core.voice.pipecat.lite_handler import LiteVoiceHandler
    from super.core.voice.processors.streaming_text_parser import (
        StreamingTextParserProcessor,
    )


class StreamingParserPlugin(PipelinePlugin):
    """
    Streaming parser plugin for voice pipeline.

    Adds StreamingTextParserProcessor to enable TTS synthesis while
    LLM is still generating, reducing latency by 500-1500ms.

    Config options:
        streamable_fields: Fields to stream (default: spoke_response, response, etc.)
        min_chunk_size: Minimum characters per chunk (default: 1)
        enabled: Whether streaming is enabled (default: True)
    """

    name = "streaming"
    priority = PluginPriority.POST_LLM

    def __init__(
        self,
        config: Optional[PluginConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        super().__init__(config, logger)
        self._processor: Optional["StreamingTextParserProcessor"] = None

    async def initialize(self, handler: "LiteVoiceHandler") -> None:
        """Initialize streaming parser plugin."""
        await super().initialize(handler)

        # Get config options
        streamable_fields = self.options.get(
            "streamable_fields",
            ["spoke_response", "response", "text", "answer", "content"],
        )
        min_chunk_size = self.options.get("min_chunk_size", 1)

        # Create streaming parser processor
        from super.core.voice.processors.streaming_text_parser import (
            create_streaming_parser_processor,
        )

        self._processor = create_streaming_parser_processor(
            streamable_fields=streamable_fields,
            min_chunk_size=min_chunk_size,
            enabled=self._config.enabled,
            logger=self._logger,
        )

        self._logger.info(
            f"StreamingParserPlugin initialized "
            f"(fields={streamable_fields}, chunk_size={min_chunk_size})"
        )

    def get_processors(self) -> List:
        """Return streaming parser processor for pipeline insertion."""
        if self._processor and self._config.enabled:
            return [self._processor]
        return []

    def get_metrics(self) -> Optional[dict]:
        """Get streaming parser metrics."""
        if self._processor:
            return self._processor.get_metrics()
        return None

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable streaming parser at runtime.

        Args:
            enabled: Whether to enable streaming parsing.
        """
        super().set_enabled(enabled)
        if self._processor:
            self._processor.set_enabled(enabled)

    async def cleanup(self) -> None:
        """Clean up streaming parser plugin resources."""
        self._processor = None
        await super().cleanup()
