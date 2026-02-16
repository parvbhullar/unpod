"""
Base plugin protocol and configuration for voice pipeline plugins.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import IntEnum
from typing import TYPE_CHECKING, Any, Optional
import logging

if TYPE_CHECKING:
    from super.core.voice.pipecat.lite_handler import LiteVoiceHandler


class PluginPriority(IntEnum):
    """Plugin execution order in pipeline. Lower = earlier."""

    FIRST = 0  # Before STT output
    PRE_LLM = 10  # After STT, before LLM (e.g., RAG enrichment)
    POST_LLM = 20  # After LLM output (e.g., streaming parser)
    PRE_TTS = 30  # Before TTS (e.g., text filtering)
    POST_TTS = 40  # After TTS (e.g., silence trimmer)
    LAST = 50  # Final processing


@dataclass
class PluginConfig:
    """Configuration for a pipeline plugin."""

    enabled: bool = True
    priority: int = PluginPriority.POST_LLM
    options: dict = field(default_factory=dict)


class PipelinePlugin(ABC):
    """
    Base class for voice pipeline plugins.

    Plugins extend the voice pipeline with optional features without
    bloating the core handler. They can:
    - Add processors to the pipeline
    - Hook into lifecycle events
    - Access handler state and services

    Example:
        class MyPlugin(PipelinePlugin):
            name = "my_plugin"
            priority = PluginPriority.POST_LLM

            async def initialize(self, handler):
                self._processor = MyProcessor()

            def get_processors(self):
                return [self._processor]
    """

    name: str = "base_plugin"
    priority: int = PluginPriority.POST_LLM

    def __init__(
        self,
        config: Optional[PluginConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self._config = config or PluginConfig()
        self._logger = logger or logging.getLogger(f"plugin.{self.name}")
        self._handler: Optional["LiteVoiceHandler"] = None
        self._initialized = False

    @property
    def enabled(self) -> bool:
        """Check if plugin is enabled."""
        return self._config.enabled

    @property
    def options(self) -> dict:
        """Get plugin options."""
        return self._config.options

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the plugin at runtime.

        Args:
            enabled: Whether to enable the plugin.
        """
        self._config.enabled = enabled
        self._logger.info(f"Plugin {self.name} {'enabled' if enabled else 'disabled'}")

    async def initialize(self, handler: "LiteVoiceHandler") -> None:
        """
        Initialize the plugin with handler reference.

        Called when plugin is activated. Override to set up resources.

        Args:
            handler: The LiteVoiceHandler instance
        """
        self._handler = handler
        self._initialized = True
        self._logger.debug(f"Plugin {self.name} initialized")

    def get_processors(self) -> list:
        """
        Return processors to insert into pipeline.

        Called during pipeline construction. Override to provide
        pipecat processors that should be added at this plugin's priority.

        Returns:
            List of pipecat processor instances
        """
        return []

    async def on_call_start(self) -> None:
        """Called when a call starts (first participant joins)."""
        pass

    async def on_call_end(self) -> None:
        """Called when a call ends."""
        pass

    async def on_user_speech(self, text: str) -> None:
        """Called when user speech is transcribed."""
        pass

    async def on_agent_speech(self, text: str) -> None:
        """Called when agent generates speech."""
        pass

    async def cleanup(self) -> None:
        """
        Clean up plugin resources.

        Called on handler shutdown. Override to release resources.
        """
        self._initialized = False
        self._handler = None
        self._logger.debug(f"Plugin {self.name} cleaned up")

    def get_metrics(self) -> Optional[dict]:
        """
        Return plugin metrics for observability.

        Override to provide timing/count metrics.

        Returns:
            Dict with metric names and values, or None
        """
        return None

    def __repr__(self) -> str:
        status = "enabled" if self.enabled else "disabled"
        return f"{self.__class__.__name__}(name={self.name}, priority={self.priority}, {status})"
