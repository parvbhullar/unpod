"""
Idle Detector Plugin - Detects user idle state.

Wraps pipecat's UserIdleProcessor to integrate with the plugin system.
"""

import logging
from typing import TYPE_CHECKING, Callable, List, Optional

from super.core.voice.plugins.base import PipelinePlugin, PluginConfig, PluginPriority

if TYPE_CHECKING:
    from pipecat.processors.user_idle_processor import UserIdleProcessor

    from super.core.voice.pipecat.lite_handler import LiteVoiceHandler


class IdleDetectorPlugin(PipelinePlugin):
    """
    Idle detector plugin for voice pipeline.

    Adds UserIdleProcessor to detect when users go idle and trigger
    appropriate actions (like prompts or call termination).

    Config options:
        timeout: Idle timeout in seconds (default: 30.0)
        callback: Optional callback function when idle detected
    """

    name = "idle"
    priority = PluginPriority.LAST

    def __init__(
        self,
        config: Optional[PluginConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        super().__init__(config, logger)
        self._processor: Optional["UserIdleProcessor"] = None
        self._idle_callback: Optional[Callable] = None

    async def initialize(self, handler: "LiteVoiceHandler") -> None:
        """Initialize idle detector plugin."""
        await super().initialize(handler)

        # Get config options
        timeout = self.options.get("timeout", 30.0)

        # Create default idle callback
        async def default_idle_callback(processor):
            self._logger.info(f"User idle detected after {timeout}s")
            if handler and handler.task:
                from pipecat.frames.frames import TTSSpeakFrame

                await handler.task.queue_frame(
                    TTSSpeakFrame("Are you still there? Let me know if you need help.")
                )

        self._idle_callback = self.options.get("callback", default_idle_callback)

        # Create idle processor
        from pipecat.processors.user_idle_processor import UserIdleProcessor

        self._processor = UserIdleProcessor(
            callback=self._idle_callback,
            timeout=timeout,
        )

        self._logger.info(f"IdleDetectorPlugin initialized (timeout={timeout}s)")

    def get_processors(self) -> List:
        """Return idle processor for pipeline insertion."""
        if self._processor and self._config.enabled:
            return [self._processor]
        return []

    def set_callback(self, callback: Callable) -> None:
        """Set custom idle callback."""
        self._idle_callback = callback
        if self._processor:
            self._processor._callback = callback

    def get_metrics(self) -> Optional[dict]:
        """Get idle detector metrics."""
        return {
            "enabled": self._config.enabled,
            "timeout": self.options.get("timeout", 30.0),
        }

    async def cleanup(self) -> None:
        """Clean up idle detector plugin resources."""
        self._processor = None
        self._idle_callback = None
        await super().cleanup()
