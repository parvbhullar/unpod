"""
Superkik Agentic Backbone for voice integration.

Uses native Python bindings (PyO3) for direct Rust integration,
providing high-performance agentic reasoning without subprocess overhead.
"""

from __future__ import annotations

import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from super.core.voice.superkik.handler import SuperKikHandler
    from super.core.voice.superkik.tools.base import ToolPluginRegistry

# Check if native superkik bindings are available
try:
    from superkik._native import (
        ApprovalPolicy,
        Event,
        EventIterator,
        ProviderType,
        SandboxPolicy,
        Session,
        SessionBuilder,
    )

    SUPERKIK_AVAILABLE = True
except ImportError:
    SUPERKIK_AVAILABLE = False
    Session = None  # type: ignore
    SessionBuilder = None  # type: ignore
    Event = Any  # type: ignore


from super.core.voice.superkik.event_bridge import SuperkikEventBridge


class SuperkikBackbone:
    """
    Agentic backbone using native superkik Python bindings (PyO3).

    Manages:
    - Native session lifecycle via SessionBuilder/Session
    - Event streaming to LiveKit voice
    - Direct Rust execution without subprocess overhead

    Usage:
        backbone = SuperkikBackbone(handler)
        await backbone.initialize()
        await backbone.process_input("Find me a dentist nearby")
        await backbone.cleanup()
    """

    def __init__(
        self,
        handler: "SuperKikHandler",
        logger: Optional[logging.Logger] = None,
    ):
        self._handler = handler
        self._logger = logger or logging.getLogger("superkik.backbone")

        self._session: Optional["Session"] = None
        self._event_bridge: Optional[SuperkikEventBridge] = None
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="superkik")

        # State
        self._initialized = False
        self._session_id: Optional[str] = None

    @property
    def available(self) -> bool:
        """Check if superkik native bindings are available."""
        return SUPERKIK_AVAILABLE

    @property
    def initialized(self) -> bool:
        """Check if backbone is initialized."""
        return self._initialized

    @property
    def session_id(self) -> Optional[str]:
        """Get current session ID."""
        return self._session_id

    async def initialize(self) -> bool:
        """
        Initialize native superkik session.

        Returns:
            True if initialization succeeded
        """
        if not SUPERKIK_AVAILABLE:
            self._logger.warning(
                "superkik native bindings not available. "
                "Build with: cd superkik/bindings/python && maturin develop"
            )
            return False

        try:
            # Create event bridge
            self._event_bridge = SuperkikEventBridge(
                self._handler,
                logger=self._logger.getChild("events"),
            )

            self._initialized = True
            self._logger.info("Superkik backbone initialized (native bindings)")
            return True

        except Exception as e:
            self._logger.error(f"Failed to initialize superkik backbone: {e}")
            self._initialized = False
            return False

    def _get_model(self) -> str:
        """Get model from handler configuration."""
        handler_config = getattr(self._handler, "superkik_config", None)
        model = "claude-sonnet-4-20250514"
        if handler_config:
            model = getattr(handler_config, "model", model) or model
        return model

    def _get_cwd(self) -> str:
        """Get working directory from handler configuration."""
        handler_config = getattr(self._handler, "superkik_config", None)
        cwd = "."
        if handler_config:
            workspace = getattr(handler_config, "workspace_path", None)
            if workspace:
                cwd = str(workspace)
        return cwd

    def _build_system_prompt(self) -> str:
        """Build system prompt from handler configuration."""
        try:
            from super.core.voice.superkik.prompts import get_superkik_prompt

            handler_config = getattr(self._handler, "superkik_config", None)
            agent_name = "SuperKik"
            if handler_config:
                agent_name = getattr(handler_config, "agent_name", agent_name) or agent_name

            return get_superkik_prompt(
                agent_name=agent_name,
                agent_context=None,
                capabilities=None,
            )
        except Exception as e:
            self._logger.warning(f"Failed to build prompt: {e}")
            return "You are a helpful voice assistant."

    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment."""
        return os.environ.get("ANTHROPIC_API_KEY")

    def _spawn_session(self) -> "Session":
        """Spawn a native superkik session (blocking, run in executor)."""
        builder = SessionBuilder(model=self._get_model(), cwd=self._get_cwd())

        # Set system prompt
        system_prompt = self._build_system_prompt()
        builder = builder.system_prompt(system_prompt)

        # Set policies - voice mode: no approval, sandboxed
        builder = builder.approval_policy(ApprovalPolicy.Never)
        builder = builder.sandbox_policy(SandboxPolicy.Full)

        # Set API key if available
        api_key = self._get_api_key()
        if api_key:
            builder = builder.api_key(api_key)

        return builder.spawn()

    async def start_session(self) -> None:
        """Start native superkik session."""
        if not self._initialized:
            raise RuntimeError("Backbone not initialized")

        loop = asyncio.get_event_loop()
        self._session = await loop.run_in_executor(self._executor, self._spawn_session)
        self._logger.info("Superkik native session started")

    async def process_input(self, user_input: str) -> str:
        """
        Process user input through native superkik session.

        Args:
            user_input: User's transcribed speech

        Returns:
            Agent's final response
        """
        if not self._initialized:
            raise RuntimeError("Backbone not initialized")

        if not self._session:
            await self.start_session()

        if not self._session or not self._event_bridge:
            raise RuntimeError("Session not started")

        final_response = ""
        loop = asyncio.get_event_loop()

        try:
            # Send message (blocking call, run in executor)
            await loop.run_in_executor(
                self._executor, self._session.send_message, user_input
            )

            # Get event iterator (blocking call, run in executor)
            event_iter = await loop.run_in_executor(
                self._executor, self._session.events
            )

            # Process events
            while True:
                try:
                    # Get next event (blocking)
                    event = await loop.run_in_executor(
                        self._executor, self._get_next_event, event_iter
                    )
                    if event is None:
                        break

                    event_type = event.event_type
                    event_data = event.as_dict()

                    # Track session ID
                    if event_type == "session_configured":
                        data = event_data.get("data", {})
                        self._session_id = data.get("session_id")

                    # Bridge event to LiveKit
                    await self._event_bridge.process_native_event(event)

                    # Capture final response
                    if event_type == "agent_message":
                        data = event_data.get("data", {})
                        final_response = data.get("message", "")

                    # Break on terminal events
                    if event_type in ("task_complete", "turn_aborted", "error"):
                        break

                except StopIteration:
                    break

        except Exception as e:
            self._logger.error(f"Error processing input: {e}")
            final_response = f"I encountered an error: {e}"

        return final_response

    def _get_next_event(self, event_iter: "EventIterator") -> Optional["Event"]:
        """Get next event from iterator (blocking helper for executor)."""
        try:
            return next(event_iter)
        except StopIteration:
            return None

    async def interrupt(self) -> None:
        """Interrupt current processing."""
        if self._session:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(self._executor, self._session.interrupt)
            except Exception as e:
                self._logger.error(f"Failed to interrupt: {e}")

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self._event_bridge:
            self._event_bridge.reset()

        if self._session:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(self._executor, self._session.shutdown)
            except Exception as e:
                self._logger.error(f"Error shutting down session: {e}")

        self._session = None
        self._event_bridge = None
        self._initialized = False
        self._session_id = None

        # Shutdown executor
        self._executor.shutdown(wait=False)

        self._logger.info("Superkik backbone cleaned up")

    async def __aenter__(self) -> "SuperkikBackbone":
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.cleanup()
