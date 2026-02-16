"""
Lazy service factory for voice services (STT, LLM, TTS).

Creates services on-demand rather than at startup to reduce initialization time.
Delegates to ServiceFactory for actual service creation to reuse all provider logic.
"""

import asyncio
import logging
from typing import Any, Callable, Optional

from pipecat.services.llm_service import LLMService
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext

from super.core.voice.pipecat.services import ServiceFactory


class LazyServiceFactory:
    """
    Factory for creating voice services with lazy initialization.

    Services are created on first access, not at construction time.
    This reduces startup latency from ~700ms to ~50ms.

    Delegates to ServiceFactory for actual service creation, ensuring
    consistent behavior with all language/provider configurations.

    Supports realtime mode:
    - Full realtime: Only LLM created (integrated audio I/O)
    - Mixed realtime: LLM + TTS created (realtime handles STT)
    - Standard: STT + LLM + TTS created

    Example:
        factory = LazyServiceFactory(config, logger)
        stt = await factory.get_stt()  # Created here, not in __init__
        llm = await factory.get_llm()  # Created on demand
    """

    def __init__(
        self,
        config: dict,
        logger: Optional[logging.Logger] = None,
        get_docs_callback: Optional[Callable] = None,
        assistant_prompt: Optional[str] = None,
    ):
        self._config = config
        self._logger = logger or logging.getLogger("services.factory")
        self._get_docs_callback = get_docs_callback
        self._assistant_prompt = assistant_prompt

        # Realtime mode flags from config
        self._use_realtime = config.get("use_realtime", False)
        self._mixed_realtime_mode = config.get("mixed_realtime_mode", False)

        # Underlying ServiceFactory for actual service creation
        self._service_factory: Optional[ServiceFactory] = None

        # Cached service instances
        self._stt: Optional[Any] = None
        self._llm: Optional[LLMService] = None
        self._tts: Optional[Any] = None
        self._context_aggregator: Optional[Any] = None

        # Creation locks to prevent concurrent creation
        self._stt_lock = asyncio.Lock()
        self._llm_lock = asyncio.Lock()
        self._tts_lock = asyncio.Lock()

        # Track initialization state
        self._stt_ready = asyncio.Event()
        self._llm_ready = asyncio.Event()
        self._tts_ready = asyncio.Event()

    def _get_service_factory(self) -> ServiceFactory:
        """Get or create the underlying ServiceFactory."""
        if self._service_factory is None:
            self._service_factory = ServiceFactory(
                config=self._config,
                logger=self._logger,
                tool_calling=self._config.get("tool_calling", True),
                get_docs_callback=self._get_docs_callback,
            )
        return self._service_factory

    @property
    def stt(self) -> Optional[Any]:
        """Get cached STT service (None if not created)."""
        return self._stt

    @property
    def llm(self) -> Optional[LLMService]:
        """Get cached LLM service (None if not created)."""
        return self._llm

    @property
    def tts(self) -> Optional[Any]:
        """Get cached TTS service (None if not created)."""
        return self._tts

    @property
    def context_aggregator(self) -> Optional[Any]:
        """Get cached context aggregator (None if not created)."""
        return self._context_aggregator

    async def get_stt(self) -> Any:
        """
        Get or create STT service.

        Returns:
            STT service instance
        """
        if self._stt is not None:
            return self._stt

        async with self._stt_lock:
            if self._stt is not None:
                return self._stt

            self._stt = await self._create_stt()
            self._stt_ready.set()
            return self._stt

    async def get_llm(self) -> LLMService:
        """
        Get or create LLM service.

        Returns:
            LLM service instance
        """
        if self._llm is not None:
            return self._llm

        async with self._llm_lock:
            if self._llm is not None:
                return self._llm

            self._llm = await self._create_llm()
            self._llm_ready.set()
            return self._llm

    async def get_tts(self) -> Any:
        """
        Get or create TTS service.

        Returns:
            TTS service instance
        """
        if self._tts is not None:
            return self._tts

        async with self._tts_lock:
            if self._tts is not None:
                return self._tts

            self._tts = await self._create_tts()
            self._tts_ready.set()
            return self._tts

    async def get_context_aggregator(
        self,
        context: OpenAILLMContext,
        aggregation_timeout: float = 0.05,
    ) -> Any:
        """
        Get or create context aggregator.

        Args:
            context: LLM context to aggregate
            aggregation_timeout: Timeout for aggregation

        Returns:
            Context aggregator instance
        """
        if self._context_aggregator is not None:
            return self._context_aggregator

        llm = await self.get_llm()
        from pipecat.processors.aggregators.llm_response import LLMUserAggregatorParams

        self._context_aggregator = llm.create_context_aggregator(
            context,
            user_params=LLMUserAggregatorParams(
                aggregation_timeout=aggregation_timeout
            ),
        )
        return self._context_aggregator

    async def _create_stt(self) -> Any:
        """Create STT service using ServiceFactory."""
        provider = self._config.get("stt_provider", "deepgram")
        model = self._config.get("stt_model", "nova-2")
        language = self._config.get("stt_language", "en")

        self._logger.info(f"Creating STT service: {provider}/{model}/{language}")

        try:
            factory = self._get_service_factory()
            return factory._create_stt_service()
        except Exception as e:
            self._logger.error(f"Failed to create STT service ({provider}): {e}")
            raise

    async def _create_llm(self) -> LLMService:
        """Create LLM service using ServiceFactory.

        For realtime mode (OpenAI Realtime or Gemini Live), passes the
        assistant prompt to the service factory for proper initialization.
        """
        provider = self._config.get("llm_provider", "openai")
        model = self._config.get("llm_model", "gpt-4o-mini")

        self._logger.info(f"Creating LLM service: {provider}/{model}")

        try:
            factory = self._get_service_factory()

            # For realtime mode, pass assistant prompt to service factory
            if self._use_realtime and provider.lower() in ["openai", "google"]:
                if self._assistant_prompt:
                    factory._assistant_prompt = self._assistant_prompt
                    self._logger.info(
                        f"Creating LLM with assistant prompt for "
                        f"{provider.upper()} Realtime API"
                    )
                else:
                    self._logger.warning(
                        "Realtime mode enabled but no assistant prompt provided"
                    )

            return factory._create_llm_service()
        except Exception as e:
            self._logger.error(f"Failed to create LLM service ({provider}): {e}")
            raise

    async def _create_tts(self) -> Any:
        """Create TTS service using ServiceFactory with retry and fallback."""
        provider = self._config.get("tts_provider", "openai")
        model = self._config.get("tts_model", "tts-1")
        voice = self._config.get("tts_voice", "alloy")

        self._logger.info(f"Creating TTS service: {provider}/{model}/{voice}")

        try:
            factory = self._get_service_factory()
            # Use retry wrapper which includes Cartesia fallback on failure
            return await factory._create_tts_service_with_retry()
        except Exception as e:
            self._logger.error(f"Failed to create TTS service ({provider}): {e}")
            raise

    async def wait_for_stt(self, timeout: float = 10.0) -> bool:
        """Wait for STT service to be ready."""
        try:
            await asyncio.wait_for(self._stt_ready.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    async def wait_for_llm(self, timeout: float = 10.0) -> bool:
        """Wait for LLM service to be ready."""
        try:
            await asyncio.wait_for(self._llm_ready.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    async def wait_for_tts(self, timeout: float = 10.0) -> bool:
        """Wait for TTS service to be ready."""
        try:
            await asyncio.wait_for(self._tts_ready.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    def is_ready(self) -> bool:
        """Check if all required services are ready based on mode."""
        if self._use_realtime and not self._mixed_realtime_mode:
            # Full realtime: Only LLM needed
            return self._llm is not None
        elif self._use_realtime and self._mixed_realtime_mode:
            # Mixed realtime: LLM + TTS needed
            return self._llm is not None and self._tts is not None
        else:
            # Standard mode: All three needed
            return (
                self._stt is not None
                and self._llm is not None
                and self._tts is not None
            )

    def set_assistant_prompt(self, prompt: str) -> None:
        """Set assistant prompt for realtime LLM initialization."""
        self._assistant_prompt = prompt

    async def preload_stt(self) -> None:
        """
        Preload STT service (non-blocking background task).

        Call this early to have STT ready before pipeline starts.
        """
        asyncio.create_task(self.get_stt())

    async def cleanup(self) -> None:
        """Clean up all service resources."""
        # Most pipecat services don't need explicit cleanup
        # but we clear references
        self._stt = None
        self._llm = None
        self._tts = None
        self._context_aggregator = None
        self._stt_ready.clear()
        self._llm_ready.clear()
        self._tts_ready.clear()
        self._logger.debug("Services cleaned up")
