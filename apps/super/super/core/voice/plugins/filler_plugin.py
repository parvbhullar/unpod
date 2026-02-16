"""
Filler Response Plugin - Generates quick conversational fillers.

Provides immediate user engagement while the main LLM processes the full response.
Uses a fast LLM to generate 1-5 word fillers like:
- "Hmm, let me think..."
- "Got it"
- "One moment"
- "Interesting"

Supports multiple providers: openai, anthropic, google, groq

This plugin adds a FillerProcessor to the pipeline at PRE_LLM priority.
The processor intercepts TranscriptionFrame (final user speech) and generates
a filler response BEFORE the LLM starts processing, reducing perceived latency.
"""

import asyncio
import logging
import os
import time
from enum import Enum
from typing import TYPE_CHECKING, Any, List, Optional, Set

from pipecat.frames.frames import Frame, TranscriptionFrame, TTSSpeakFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from super.core.voice.plugins.base import PipelinePlugin, PluginConfig, PluginPriority

if TYPE_CHECKING:
    from super.core.voice.pipecat.lite_handler import LiteVoiceHandler


class FillerProvider(str, Enum):
    """Supported LLM providers for filler generation."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    GROQ = "groq"


# Default models per provider (fast, low-latency models)
DEFAULT_MODELS = {
    FillerProvider.OPENAI: "gpt-4o-mini",
    FillerProvider.ANTHROPIC: "claude-3-haiku-20240307",
    FillerProvider.GOOGLE: "gemini-1.5-flash",
    FillerProvider.GROQ: "llama-3.1-8b-instant",
}

# Short phrases that don't need filler responses
SKIP_PATTERNS: Set[str] = {
    # Greetings (user already greeted, agent responds with first_message)
    "hello", "hi", "hey", "hiya", "howdy",
    "good morning", "good afternoon", "good evening",
    # Acknowledgments (don't need filler)
    "yes", "no", "yeah", "nope", "ok", "okay", "sure",
    "thanks", "thank you", "got it", "understood",
    # Simple responses
    "hmm", "uh", "um", "oh", "ah",
}

FILLER_PROMPT = """Generate a brief conversational filler (1-5 words max) to acknowledge the user while processing their request.

Context from recent conversation:
{context}

User just said: "{user_message}"

Requirements:
- 1-5 words ONLY
- Natural and conversational
- Match the tone (casual vs formal)
- Examples: "Hmm", "Let me see", "Got it", "One moment", "Interesting"
- DO NOT repeat the user's words
- DO NOT answer their question

Filler response:"""


class FillerProcessor(FrameProcessor):
    """
    Processor that generates filler responses when user speech is transcribed.

    Intercepts TranscriptionFrame at PRE_LLM position in the pipeline.
    Generates a quick filler and sends TTSSpeakFrame BEFORE the LLM processes.
    """

    def __init__(
        self,
        client: Any,
        provider: FillerProvider,
        model: str,
        max_tokens: int,
        temperature: float,
        timeout: float,
        skip_patterns: Set[str],
        get_context_callback: Any,
        enabled: bool = True,
        logger: Optional[logging.Logger] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._client = client
        self._provider = provider
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._timeout = timeout
        self._skip_patterns = skip_patterns
        self._get_context_callback = get_context_callback
        self._enabled = enabled
        self._logger = logger or logging.getLogger(__name__)

        # Metrics
        self._total_requests: int = 0
        self._total_generated: int = 0
        self._total_skipped: int = 0
        self._total_timeouts: int = 0
        self._total_latency_ms: float = 0.0

    async def process_frame(
        self, frame: Frame, direction: FrameDirection
    ) -> None:
        """Process frames, generating fillers for TranscriptionFrames.

        IMPORTANT: Filler generation runs in parallel (non-blocking).
        The TranscriptionFrame is passed through immediately so the main LLM
        can start processing. Filler is generated concurrently and pushed
        when ready.
        """
        await super().process_frame(frame, direction)

        # Only process final transcription frames going downstream
        if (
            isinstance(frame, TranscriptionFrame)
            and direction == FrameDirection.DOWNSTREAM
            and self._enabled
        ):
            # Start filler generation in background - DO NOT BLOCK
            # The transcription frame continues immediately to the LLM
            asyncio.create_task(
                self._handle_transcription_async(frame),
                name=f"filler-{time.perf_counter()}"
            )

        # Always pass the frame through IMMEDIATELY (non-blocking)
        await self.push_frame(frame, direction)

    async def _handle_transcription_async(self, frame: TranscriptionFrame) -> None:
        """Handle transcription frame - generate and queue filler (runs in background).

        This method runs as a background task, NOT blocking the main pipeline.
        Uses push_frame to inject the filler into the pipeline stream.
        """
        text = frame.text
        if not text:
            return

        self._total_requests += 1
        text_normalized = text.lower().strip()

        # Skip if text matches skip patterns
        if self._should_skip(text_normalized):
            self._total_skipped += 1
            self._logger.debug(f"Filler skipped for: '{text[:30]}...'")
            return

        try:
            start_time = time.perf_counter()

            # Generate filler with timeout
            filler = await asyncio.wait_for(
                self._generate_filler(text),
                timeout=self._timeout,
            )

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            self._total_latency_ms += elapsed_ms

            if filler:
                self._total_generated += 1
                # Push filler frame downstream - it will flow through to TTS
                # Since we're in a background task, we push directly to the processor
                await self.push_frame(
                    TTSSpeakFrame(filler),
                    FrameDirection.DOWNSTREAM
                )
                self._logger.info(
                    f"Filler generated in {elapsed_ms:.0f}ms: '{filler}'"
                )
            else:
                self._logger.debug("No filler generated")

        except asyncio.TimeoutError:
            self._total_timeouts += 1
            self._logger.warning(f"Filler generation timed out ({self._timeout}s)")
        except Exception as e:
            self._logger.error(f"Filler generation error: {e}")

    def _should_skip(self, text: str) -> bool:
        """Check if text should skip filler generation."""
        # Skip very short texts (< 2 words)
        words = text.split()
        if len(words) < 2:
            return True

        # Check skip patterns
        cleaned = text.replace(".", "").replace("?", "").replace("!", "").strip()
        if cleaned in self._skip_patterns:
            return True

        # Check if starts with common greeting
        first_words = " ".join(words[:2])
        if first_words in self._skip_patterns:
            return True

        return False

    async def _generate_filler(self, user_message: str) -> Optional[str]:
        """Generate filler response using the configured LLM provider."""
        if not self._client:
            return None

        # Get recent context
        context_str = self._get_context_callback()

        # Build prompt
        prompt = FILLER_PROMPT.format(
            context=context_str,
            user_message=user_message,
        )

        try:
            if self._provider == FillerProvider.OPENAI:
                return await self._generate_openai(prompt)
            elif self._provider == FillerProvider.ANTHROPIC:
                return await self._generate_anthropic(prompt)
            elif self._provider == FillerProvider.GOOGLE:
                return await self._generate_google(prompt)
            elif self._provider == FillerProvider.GROQ:
                return await self._generate_groq(prompt)
        except Exception as e:
            self._logger.error(f"LLM filler request failed: {e}")
            return None

        return None

    async def _generate_openai(self, prompt: str) -> Optional[str]:
        """Generate filler using OpenAI."""
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self._max_tokens,
            temperature=self._temperature,
        )
        return self._validate_filler(response.choices[0].message.content)

    async def _generate_anthropic(self, prompt: str) -> Optional[str]:
        """Generate filler using Anthropic."""
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return self._validate_filler(response.content[0].text)

    async def _generate_google(self, prompt: str) -> Optional[str]:
        """Generate filler using Google Gemini."""
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self._client.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": self._max_tokens,
                    "temperature": self._temperature,
                }
            )
        )
        return self._validate_filler(response.text)

    async def _generate_groq(self, prompt: str) -> Optional[str]:
        """Generate filler using Groq."""
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self._max_tokens,
            temperature=self._temperature,
        )
        return self._validate_filler(response.choices[0].message.content)

    def _validate_filler(self, filler: Optional[str]) -> Optional[str]:
        """Validate filler is short and clean."""
        if not filler:
            return None

        filler = filler.strip().strip('"\'')

        # Validate filler is short (max 7 words)
        if len(filler.split()) <= 7:
            return filler

        self._logger.debug(f"Filler too long, discarding: '{filler}'")
        return None

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable filler generation."""
        self._enabled = enabled
        self._logger.info(f"FillerProcessor {'enabled' if enabled else 'disabled'}")

    def get_metrics(self) -> dict:
        """Get filler processor metrics."""
        avg_latency = (
            self._total_latency_ms / self._total_generated
            if self._total_generated > 0
            else 0.0
        )

        return {
            "total_requests": self._total_requests,
            "total_generated": self._total_generated,
            "total_skipped": self._total_skipped,
            "total_timeouts": self._total_timeouts,
            "avg_latency_ms": round(avg_latency, 2),
            "enabled": self._enabled,
            "provider": self._provider.value,
            "model": self._model,
        }


class FillerResponsePlugin(PipelinePlugin):
    """
    Plugin that generates quick filler responses for immediate user engagement.

    When the user speaks, this plugin immediately generates a brief
    conversational filler (1-5 words) and sends it to TTS. This provides
    instant feedback while the main LLM processes the full response.

    The plugin works by adding a FillerProcessor to the pipeline at PRE_LLM
    priority. The processor intercepts TranscriptionFrame and generates
    a filler BEFORE the LLM starts processing.

    Supported providers:
        - openai: OpenAI GPT models (default: gpt-4o-mini)
        - anthropic: Anthropic Claude models (default: claude-3-haiku)
        - google: Google Gemini models (default: gemini-1.5-flash)
        - groq: Groq models (default: llama-3.1-8b-instant)

    Config options:
        enabled: Whether filler generation is enabled (default: True)
        provider: LLM provider (default: openai)
        model: LLM model for filler generation (default: provider-specific)
        max_tokens: Maximum tokens for filler (default: 10)
        temperature: LLM temperature (default: 0.7)
        timeout: Filler generation timeout in seconds (default: 0.5)
        skip_patterns: Additional patterns to skip (list of strings)

    Environment variables:
        FILLER_ENABLED: Enable/disable plugin (true/false)
        FILLER_PROVIDER: LLM provider (openai/anthropic/google/groq)
        FILLER_MODEL: Model name (provider-specific)
        FILLER_MAX_TOKENS: Max tokens (default: 10)
        FILLER_TEMPERATURE: Temperature (default: 0.7)
        FILLER_TIMEOUT: Timeout in seconds (default: 0.5)
        FILLER_SKIP_PATTERNS: Comma-separated patterns to skip
    """

    name = "filler"
    priority = PluginPriority.PRE_LLM  # Before main LLM in pipeline

    def __init__(
        self,
        config: Optional[PluginConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        super().__init__(config, logger)
        self._client: Any = None
        self._provider: FillerProvider = FillerProvider.OPENAI
        self._model: str = "gpt-4o-mini"
        self._max_tokens: int = 10
        self._temperature: float = 0.7
        self._timeout: float = 0.5
        self._skip_patterns: Set[str] = SKIP_PATTERNS.copy()
        self._processor: Optional[FillerProcessor] = None

    async def initialize(self, handler: "LiteVoiceHandler") -> None:
        """Initialize filler plugin with LLM client."""
        await super().initialize(handler)

        # Get provider from env/config
        provider_str = os.getenv(
            "FILLER_PROVIDER",
            self.options.get("provider", "openai")
        ).lower()

        try:
            self._provider = FillerProvider(provider_str)
        except ValueError:
            self._logger.warning(
                f"Unknown provider '{provider_str}', falling back to openai"
            )
            self._provider = FillerProvider.OPENAI

        # Get model (use provider default if not specified)
        default_model = DEFAULT_MODELS.get(self._provider, "gpt-4o-mini")
        self._model = os.getenv(
            "FILLER_MODEL",
            self.options.get("model", default_model)
        )

        # Get other config
        self._max_tokens = int(os.getenv(
            "FILLER_MAX_TOKENS",
            self.options.get("max_tokens", 10)
        ))
        self._temperature = float(os.getenv(
            "FILLER_TEMPERATURE",
            self.options.get("temperature", 0.7)
        ))
        self._timeout = float(os.getenv(
            "FILLER_TIMEOUT",
            self.options.get("timeout", 0.5)
        ))

        # Check if filler is enabled via env (can override config)
        filler_enabled_env = os.getenv("FILLER_ENABLED", "").lower()
        if filler_enabled_env == "false":
            self._config.enabled = False
        elif filler_enabled_env == "true":
            self._config.enabled = True

        # Add custom skip patterns from env (comma-separated)
        env_skip_patterns = os.getenv("FILLER_SKIP_PATTERNS", "")
        if env_skip_patterns:
            for pattern in env_skip_patterns.split(","):
                self._skip_patterns.add(pattern.lower().strip())

        # Add custom skip patterns from config
        custom_skip = self.options.get("skip_patterns", [])
        for pattern in custom_skip:
            self._skip_patterns.add(pattern.lower().strip())

        # Initialize provider client
        await self._init_client()

        # Create processor if client initialized successfully
        if self._client and self._config.enabled:
            self._processor = FillerProcessor(
                client=self._client,
                provider=self._provider,
                model=self._model,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
                timeout=self._timeout,
                skip_patterns=self._skip_patterns,
                get_context_callback=self._get_recent_context,
                enabled=self._config.enabled,
                logger=self._logger,
            )
            self._logger.info(
                f"FillerPlugin initialized with processor "
                f"(provider={self._provider.value}, model={self._model})"
            )

    async def _init_client(self) -> None:
        """Initialize the LLM client based on provider."""
        try:
            if self._provider == FillerProvider.OPENAI:
                await self._init_openai()
            elif self._provider == FillerProvider.ANTHROPIC:
                await self._init_anthropic()
            elif self._provider == FillerProvider.GOOGLE:
                await self._init_google()
            elif self._provider == FillerProvider.GROQ:
                await self._init_groq()
            else:
                self._logger.warning(f"Unknown provider: {self._provider}")
                self._config.enabled = False

        except ImportError as e:
            self._logger.warning(
                f"FillerPlugin: Required package not installed for {self._provider}: {e}"
            )
            self._config.enabled = False
        except Exception as e:
            self._logger.error(f"FillerPlugin init failed: {e}")
            self._config.enabled = False

    async def _init_openai(self) -> None:
        """Initialize OpenAI client."""
        import openai

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            self._logger.warning("OPENAI_API_KEY not found, filler plugin disabled")
            self._config.enabled = False
            return

        self._client = openai.AsyncOpenAI(api_key=api_key)
        self._logger.info(
            f"FillerPlugin client initialized (provider=openai, model={self._model})"
        )

    async def _init_anthropic(self) -> None:
        """Initialize Anthropic client."""
        import anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            self._logger.warning("ANTHROPIC_API_KEY not found, filler plugin disabled")
            self._config.enabled = False
            return

        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._logger.info(
            f"FillerPlugin client initialized (provider=anthropic, model={self._model})"
        )

    async def _init_google(self) -> None:
        """Initialize Google Gemini client."""
        import google.generativeai as genai

        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            self._logger.warning(
                "GOOGLE_API_KEY/GEMINI_API_KEY not found, filler plugin disabled"
            )
            self._config.enabled = False
            return

        genai.configure(api_key=api_key)
        self._client = genai.GenerativeModel(self._model)
        self._logger.info(
            f"FillerPlugin client initialized (provider=google, model={self._model})"
        )

    async def _init_groq(self) -> None:
        """Initialize Groq client."""
        from groq import AsyncGroq

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            self._logger.warning("GROQ_API_KEY not found, filler plugin disabled")
            self._config.enabled = False
            return

        self._client = AsyncGroq(api_key=api_key)
        self._logger.info(
            f"FillerPlugin client initialized (provider=groq, model={self._model})"
        )

    def get_processors(self) -> List:
        """Return the filler processor for pipeline insertion."""
        if self._processor and self._config.enabled:
            return [self._processor]
        return []

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable filler plugin at runtime."""
        super().set_enabled(enabled)
        if self._processor:
            self._processor.set_enabled(enabled)

    def _get_recent_context(self) -> str:
        """Get last 2 conversation turns for context."""
        if not self._handler or not self._handler.user_state:
            return "No prior context"

        transcript = getattr(self._handler.user_state, "transcript", [])
        if not transcript:
            return "No prior context"

        # Get last 2 entries
        recent = transcript[-2:] if len(transcript) >= 2 else transcript
        context_parts = []
        for entry in recent:
            role = entry.get("role", "unknown")
            content = entry.get("content", "")[:100]  # Truncate
            context_parts.append(f"{role}: {content}")

        return "\n".join(context_parts) if context_parts else "No prior context"

    def get_metrics(self) -> Optional[dict]:
        """Get filler plugin metrics."""
        if self._processor:
            return self._processor.get_metrics()

        # Return basic metrics if no processor
        return {
            "enabled": self._config.enabled,
            "provider": self._provider.value,
            "model": self._model,
            "processor_created": self._processor is not None,
        }

    async def cleanup(self) -> None:
        """Clean up filler plugin resources."""
        self._client = None
        self._processor = None
        await super().cleanup()
