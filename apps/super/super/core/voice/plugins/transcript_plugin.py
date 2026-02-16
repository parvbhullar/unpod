"""
Transcript Plugin - Manages transcript processing and storage.

Provides transcript processing for voice pipeline with callback support.
"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from pipecat.processors.transcript_processor import TranscriptProcessor

from super.core.voice.plugins.base import PipelinePlugin, PluginConfig, PluginPriority

if TYPE_CHECKING:
    from super.core.voice.pipecat.lite_handler import LiteVoiceHandler


class TranscriptPlugin(PipelinePlugin):
    """
    Transcript plugin for voice pipeline.

    Manages TranscriptProcessor and provides hooks for transcript events.
    Stores transcript history and provides callback integration.

    Config options:
        store_transcript: Whether to store transcripts (default: True)
        max_history: Maximum transcript entries to keep (default: 1000)
    """

    name = "transcript"
    priority = PluginPriority.LAST

    def __init__(
        self,
        config: Optional[PluginConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        super().__init__(config, logger)
        self._processor: Optional[TranscriptProcessor] = None
        self._transcript_history: List[Dict[str, Any]] = []
        self._on_user_message: Optional[Callable] = None
        self._on_assistant_message: Optional[Callable] = None

    async def initialize(self, handler: "LiteVoiceHandler") -> None:
        """Initialize transcript plugin."""
        await super().initialize(handler)

        # Get config options
        self._store_transcript = self.options.get("store_transcript", True)
        self._max_history = self.options.get("max_history", 1000)

        # Create transcript processor
        self._processor = TranscriptProcessor()

        # Set up event handler
        self._setup_transcript_handler()

        self._logger.info("TranscriptPlugin initialized")

    def _setup_transcript_handler(self) -> None:
        """Set up transcript event handler."""
        if not self._processor:
            return

        @self._processor.event_handler("on_transcript_update")
        async def handle_update(processor, frame):
            for message in frame.messages:
                # Store transcript entry
                if self._store_transcript:
                    entry = {
                        "role": message.role,
                        "content": message.content,
                        "timestamp": datetime.now().isoformat(),
                    }
                    self._transcript_history.append(entry)

                    # Trim history if needed
                    if len(self._transcript_history) > self._max_history:
                        self._transcript_history = self._transcript_history[
                            -self._max_history :
                        ]

                # Call registered callbacks
                if message.role == "user" and self._on_user_message:
                    await self._on_user_message(message.content)
                elif message.role == "assistant" and self._on_assistant_message:
                    await self._on_assistant_message(message.content)

    def get_processors(self) -> List:
        """Return transcript processors for pipeline insertion."""
        if self._processor and self._config.enabled:
            return [self._processor.user(), self._processor.assistant()]
        return []

    def register_user_callback(self, callback: Callable) -> None:
        """Register callback for user messages."""
        self._on_user_message = callback

    def register_assistant_callback(self, callback: Callable) -> None:
        """Register callback for assistant messages."""
        self._on_assistant_message = callback

    def get_transcript_history(self) -> List[Dict[str, Any]]:
        """Get full transcript history."""
        return self._transcript_history.copy()

    def get_last_n_messages(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get last N transcript messages."""
        return self._transcript_history[-n:]

    async def on_call_start(self) -> None:
        """Clear transcript on call start."""
        self._transcript_history.clear()
        self._logger.debug("Transcript history cleared")

    def get_metrics(self) -> Optional[dict]:
        """Get transcript metrics."""
        user_count = sum(
            1 for t in self._transcript_history if t.get("role") == "user"
        )
        assistant_count = sum(
            1 for t in self._transcript_history if t.get("role") == "assistant"
        )
        return {
            "total_messages": len(self._transcript_history),
            "user_messages": user_count,
            "assistant_messages": assistant_count,
            "enabled": self._config.enabled,
        }

    async def cleanup(self) -> None:
        """Clean up transcript plugin resources."""
        self._processor = None
        self._transcript_history.clear()
        self._on_user_message = None
        self._on_assistant_message = None
        await super().cleanup()
