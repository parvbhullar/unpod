"""
Silence Trimmer Plugin - Trims leading silence from TTS audio.

Wraps SilenceTrimmerProcessor to integrate with the plugin system.
"""

import logging
from typing import TYPE_CHECKING, List, Optional

from super.core.voice.plugins.base import PipelinePlugin, PluginConfig, PluginPriority

if TYPE_CHECKING:
    from super.core.voice.pipecat.lite_handler import LiteVoiceHandler
    from super.core.voice.processors.silence_trimmer import SilenceTrimmerProcessor


class SilenceTrimmerPlugin(PipelinePlugin):
    """
    Silence trimmer plugin for voice pipeline.

    Adds SilenceTrimmerProcessor to trim leading silence from TTS audio,
    reducing perceived latency by 100-300ms.

    Config options:
        threshold_db: Silence threshold in dB (default: -50.0)
        sample_rate: Audio sample rate (default: 24000)
        chunk_size_ms: Analysis chunk size (default: 10)
    """

    name = "silence"
    priority = PluginPriority.POST_TTS

    def __init__(
        self,
        config: Optional[PluginConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        super().__init__(config, logger)
        self._processor: Optional["SilenceTrimmerProcessor"] = None

    async def initialize(self, handler: "LiteVoiceHandler") -> None:
        """Initialize silence trimmer plugin."""
        await super().initialize(handler)

        # Get config options
        threshold_db = self.options.get("threshold_db", -50.0)
        sample_rate = self.options.get("sample_rate", 24000)
        chunk_size_ms = self.options.get("chunk_size_ms", 10)

        # Create silence trimmer processor
        from super.core.voice.processors.silence_trimmer import create_silence_trimmer

        self._processor = create_silence_trimmer(
            silence_threshold_db=threshold_db,
            sample_rate=sample_rate,
            chunk_size_ms=chunk_size_ms,
            enabled=self._config.enabled,
            logger=self._logger,
        )

        self._logger.info(
            f"SilenceTrimmerPlugin initialized "
            f"(threshold={threshold_db}dB, sample_rate={sample_rate})"
        )

    def get_processors(self) -> List:
        """Return silence trimmer processor for pipeline insertion."""
        if self._processor and self._config.enabled:
            return [self._processor]
        return []

    async def on_call_start(self) -> None:
        """Reset metrics on call start."""
        if self._processor:
            self._processor.reset_metrics()

    def get_metrics(self) -> Optional[dict]:
        """Get silence trimmer metrics."""
        if self._processor:
            return self._processor.get_metrics()
        return None

    async def cleanup(self) -> None:
        """Clean up silence trimmer plugin resources."""
        self._processor = None
        await super().cleanup()
