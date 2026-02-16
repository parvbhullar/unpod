"""
Base Agent Handler - Abstract base class for voice/chat agent handlers.

This module provides common lifecycle management for agent handlers:
- Config resolution (from metadata or SIP attributes)
- Task tracking and cleanup
- ServiceCache access (VAD, embeddings, STT/TTS/LLM)
- Agent state signaling to LiveKit

Subclasses:
- VoiceAgentHandler: Pipecat/LiveKit voice handlers
- SuperkikAgentHandler: Superkik-py native bindings with voice+chat
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional, Set
import asyncio
import logging

# Re-export AgentConfigResult from common config_resolver
from super.core.voice.common.config_resolver import (
    AgentConfigResult,
    resolve_agent_config,
)

if TYPE_CHECKING:
    from livekit.agents import JobContext


class BaseAgentHandler(ABC):
    """
    Abstract base class for agent handlers.

    Provides common lifecycle management:
    - Task tracking for proper cleanup
    - ServiceCache access for shared resources
    - Abstract interface for entrypoint, message handling, and interrupts
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
        handler_type: str = "base",
    ) -> None:
        """
        Initialize the base agent handler.

        Args:
            session_id: Unique session identifier
            logger: Logger instance (defaults to module logger)
            handler_type: Type identifier (e.g., "superkik", "pipecat", "livekit")
        """
        self._session_id = session_id
        self._logger = logger or logging.getLogger(__name__)
        self.handler_type = handler_type
        self._job_context: Optional["JobContext"] = None
        self._pending_tasks: Set[asyncio.Task] = set()
        self._is_shutting_down: bool = False

    @abstractmethod
    async def entrypoint(self, ctx: "JobContext") -> None:
        """
        Main entry point called by LiveKit agent worker.

        Args:
            ctx: LiveKit JobContext with room, participant info, and metadata
        """
        ...

    @abstractmethod
    async def handle_message(self, text: str) -> None:
        """
        Handle an incoming text message from the user.

        Args:
            text: User's message text
        """
        ...

    @abstractmethod
    async def handle_interrupt(self) -> None:
        """
        Handle user interrupt (e.g., user starts speaking while agent is responding).

        Should cancel ongoing generation and TTS playback.
        """
        ...

    def _track_task(self, task: asyncio.Task) -> asyncio.Task:
        """
        Track an async task for cleanup on shutdown.

        Args:
            task: The asyncio.Task to track

        Returns:
            The same task (for chaining)
        """
        self._pending_tasks.add(task)
        task.add_done_callback(self._pending_tasks.discard)
        return task

    async def _cancel_pending_tasks(self, timeout: float = 5.0) -> int:
        """
        Cancel all pending tracked tasks gracefully.

        Args:
            timeout: Maximum time to wait for tasks to complete

        Returns:
            Number of tasks cancelled
        """
        if not self._pending_tasks:
            return 0

        tasks_to_cancel = list(self._pending_tasks)
        cancelled = 0

        for task in tasks_to_cancel:
            if not task.done():
                task.cancel()
                cancelled += 1

        if tasks_to_cancel:
            await asyncio.wait(tasks_to_cancel, timeout=timeout)

        self._pending_tasks.clear()
        return cancelled

    def get_service_cache(self) -> Any:
        """
        Get the global ServiceCache instance.

        Returns:
            ServiceCache with pre-warmed VAD, embeddings, and cached services
        """
        from super.core.voice.voice_agent_handler import get_service_cache

        return get_service_cache()

    async def shutdown(self) -> None:
        """
        Gracefully shutdown the handler.

        Cancels pending tasks and cleans up resources.
        """
        self._is_shutting_down = True
        cancelled = await self._cancel_pending_tasks()
        if cancelled > 0:
            self._logger.info(f"Cancelled {cancelled} pending tasks during shutdown")

    @property
    def session_id(self) -> Optional[str]:
        """Get the session ID."""
        return self._session_id

    @property
    def is_shutting_down(self) -> bool:
        """Check if the handler is in shutdown state."""
        return self._is_shutting_down

    async def _resolve_agent_config(
        self,
        ctx: "JobContext",
        metadata: dict,
    ) -> Optional[AgentConfigResult]:
        """
        Resolve agent configuration from metadata.

        Delegates to the common config resolver which handles:
        - SDK/web calls with agent_handle or space_token
        - Inbound SIP calls with phone number lookup
        - Outbound calls with agent_id

        Args:
            ctx: LiveKit JobContext
            metadata: Parsed job metadata

        Returns:
            AgentConfigResult or None if resolution failed
        """
        return await resolve_agent_config(ctx, metadata)
