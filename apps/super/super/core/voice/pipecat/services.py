"""
ServiceFactory - Standalone module for creating LLM, STT, and TTS services.

This module provides a factory class for creating various AI service instances
for voice processing pipelines. It supports multiple providers for:
- LLM (Language Model) services: OpenAI, Anthropic, Azure, Gemini, Groq, Google Vertex, AWS Bedrock
- STT (Speech-to-Text) services: OpenAI, Cartesia, Fal, Gladia, Deepgram, Soniox, Google, Azure
- TTS (Text-to-Speech) services: OpenAI, Groq, Sarvam, ElevenLabs, Deepgram, Cartesia, Google, LMNT

All service creation logic follows the configurable_agent.py pattern.
"""

import os
import logging
from typing import Any, Callable, Dict, Optional
from dotenv import load_dotenv

from super.core.voice.managers.tools_manager import ToolsManager
from super.core.voice.services.service_common import (
    DEFAULT_TTS_PROVIDER,
    DEFAULT_TTS_MODEL,
    DEFAULT_TTS_VOICE,
    GEMINI_LANGUAGE_MAP,
    GEMINI_REALTIME_MODELS,
    GEMINI_REALTIME_VOICES,
    LLM_FALLBACK_CHAIN,
    STT_FALLBACK_CHAIN,
    TTS_FALLBACK_CHAIN,
    ServiceCommon,
    estimate_tokens,
    get_model_context_limit,
)

# Load environment variables
load_dotenv(override=True)

__all__ = ["ServiceFactory", "DualLanguageTTS"]

try:
    from pipecat.pipeline.parallel_pipeline import ParallelPipeline
    from pipecat.frames.frames import Frame
    from pipecat.processors.filters.function_filter import FunctionFilter
    from pipecat.services.llm_service import FunctionCallParams

    PIPECAT_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    ParallelPipeline = None
    Frame = None
    FunctionFilter = None
    FunctionCallParams = Any  # Fallback for type annotations
    PIPECAT_AVAILABLE = False

# OpenAI Realtime imports
try:
    from pipecat.services.openai.realtime.llm import OpenAIRealtimeLLMService
    from pipecat.services.openai.realtime.events import (
        AudioConfiguration,
        AudioInput,
        InputAudioNoiseReduction,
        InputAudioTranscription,
        SemanticTurnDetection,
        SessionProperties,
        AudioOutput,
    )
    from pipecat.services.openai.realtime.llm import OpenAIRealtimeLLMService

    # from pipecat.transports.base_transport import BaseTransport, TransportParams

    OPENAI_REALTIME_AVAILABLE = True
except ImportError:
    OpenAIRealtimeLLMService = None
    AudioConfiguration = None
    InputAudioTranscription = None
    InputAudioNoiseReduction = None
    AudioInput = None
    SemanticTurnDetection = None
    SessionProperties = None
    OPENAI_REALTIME_AVAILABLE = False

# Gemini Live Vertex imports
try:
    from pipecat.services.google.gemini_live.llm_vertex import GeminiLiveVertexLLMService

    GEMINI_LIVE_AVAILABLE = True
except ImportError:
    GeminiLiveVertexLLMService = None
    GEMINI_LIVE_AVAILABLE = False


class DualLanguageTTS(ParallelPipeline):
    """Route TTS output between English and a secondary language."""

    def __init__(
        self,
        english_tts,
        secondary_tts,
        secondary_language_code: str,
        logger: Optional[logging.Logger] = None,
        on_language_change: Optional[Callable[[str], None]] = None,
    ):
        self._logger = logger or logging.getLogger(__name__)
        self._secondary_language_code = (secondary_language_code or "en").lower()
        self._current_language_code = "en"
        self._on_language_change = on_language_change

        super().__init__(
            [FunctionFilter(self._route_english), english_tts],
            [FunctionFilter(self._route_secondary), secondary_tts],
        )

    async def _route_english(self, _: Frame) -> bool:
        return self._current_language_code == "en"

    async def _route_secondary(self, _: Frame) -> bool:
        return self._current_language_code != "en"

    def set_language(self, language_code: Optional[str]) -> None:
        normalized = (language_code or "").lower()
        if normalized.startswith("en"):
            target = "en"
        elif normalized:
            target = self._secondary_language_code
        else:
            target = "en"

        if target not in ("en", self._secondary_language_code):
            target = "en"

        if target != self._current_language_code:
            self._logger.debug(
                "Switching TTS language from %s to %s",
                self._current_language_code,
                target,
            )
            self._current_language_code = target
            if self._on_language_change:
                self._on_language_change(target)

    @property
    def current_language(self) -> str:
        return self._current_language_code

    async def switch_language(self, params: FunctionCallParams):
        """Function-call friendly interface for LLM tool usage."""
        requested = params.arguments.get("language") if params.arguments else None
        self.set_language(requested)
        if hasattr(params, "result_callback") and callable(params.result_callback):
            await params.result_callback(
                {
                    "voice": f"TTS language set to {self.current_language}",
                }
            )


class ServiceFactory:
    """
    Factory class for creating LLM, STT, and TTS services based on configuration.

    Supports multiple providers for each service type:
    - 7 LLM providers
    - 8 STT providers
    - 9 TTS providers
    """

    def __init__(
        self,
        config: Dict[str, Any],
        logger: Optional[logging.Logger] = None,
        room_name: Optional[str] = None,
        tool_calling: bool = False,
        use_realtime: bool = False,
        get_docs_callback: Optional[callable] = None,
    ):
        """
        Initialize the ServiceFactory.

        Args:
            config: Configuration dictionary containing provider settings
            logger: Optional logger instance for logging
            room_name: Optional room name for caching/session management
            tool_calling: Whether tool calling is enabled for LLM services
            get_docs_callback: Optional callback function for knowledge base retrieval
        """
        self.config = config
        self._logger = logger or logging.getLogger(__name__)
        self.room_name = room_name or "default_room"
        self.session_id = config.get("session_id", self.room_name)
        self.tool_calling = tool_calling

        self._common = ServiceCommon(
            config,
            logger=self._logger,
            room_name=self.room_name,
            session_id=self.session_id,
        )
        self.stt_config = self._common.stt_config
        self.llm_config = self._common.llm_config
        self.tts_config = self._common.tts_config

        # Determine realtime mode from config or environment
        # Priority: config > env > default (False)
        self.use_realtime = use_realtime

        # Mixed mode: OpenAI Realtime LLM + separate TTS (for text output -> custom TTS)
        # This allows using Realtime's superior STT/LLM with your preferred TTS provider
        self.mixed_realtime_mode = config.get(
            "mixed_realtime_mode",
            os.getenv("MIXED_REALTIME_MODE", "false").lower() == "true",
        )

        # Log mode configuration
        if self.use_realtime and self.mixed_realtime_mode:
            self._logger.info(
                "🔀 Mixed Realtime Mode: OpenAI Realtime LLM + Separate TTS"
            )
        elif self.use_realtime:
            self._logger.info(
                "⚡ Full Realtime Mode: OpenAI Realtime (integrated audio)"
            )
        else:
            self._logger.info("🔧 Standard Mode: Separate STT/LLM/TTS services")

        self.get_docs_callback = get_docs_callback
        self._secondary_language_code = self.config.get("language", None)
        self._dual_language_tts: Optional[DualLanguageTTS] = None

    def set_session_id(self, session_id: str) -> None:
        self.session_id = session_id

    def _get_voice_optimized_max_tokens(self) -> int:
        """Get voice-optimized max_tokens with validation."""
        return self._common.get_voice_optimized_max_tokens()

    def _get_voice_optimized_temperature(self) -> float:
        """Get voice-optimized temperature with validation."""
        return self._common.get_voice_optimized_temperature()

    def _build_cache_key(self) -> str:
        """Build robust cache key with session and user context."""
        user_state = getattr(self.config, "get", lambda k, d=None: d)("user_state", None)
        return self._common.build_cache_key(
            room_name=self.room_name,
            session_id=self.session_id,
            user_state=user_state,
        )

    def _create_fallback_llm(self) -> Optional[Any]:
        """
        Create fallback LLM service (OpenAI GPT-4o-mini) as last resort.

        Used when primary provider fails after retries. Provides:
        - Lower cost (GPT-4o-mini vs GPT-4o)
        - High availability (OpenAI reliability)
        - Basic voice optimization

        Returns:
            Fallback LLM service or None if even fallback fails
        """
        try:
            from pipecat.services.openai.llm import OpenAILLMService

            self._logger.warning(
                "Primary LLM failed, using fallback: OpenAI GPT-4o-mini"
            )
            return OpenAILLMService(
                api_key=os.getenv("OPENAI_API_KEY"),
                model="gpt-4o-mini",  # Cheaper fallback
                params=OpenAILLMService.InputParams(
                    temperature=0.4,  # Voice-optimized
                    max_completion_tokens=500,  # Voice-optimized
                ),
            )
        except Exception as e:
            self._logger.critical(f"Fallback LLM also failed: {e}")
            return None

    def _create_openai_realtime_llm_service(
        self, assistant_prompt: Optional[str] = None
    ) -> Optional[Any]:
        """
        Create OpenAI Realtime LLM service with audio configuration.

        The Realtime API provides:
        - Native audio input/output (no separate STT/TTS needed)
        - Lower latency (end-to-end voice)
        - Semantic turn detection
        - Function calling support

        Args:
            assistant_prompt: Full prompt from prompt_manager (system + assistant)

        Returns:
            OpenAIRealtimeLLMService instance or None on failure
        """
        if not OPENAI_REALTIME_AVAILABLE:
            self._logger.error(
                "OpenAI Realtime API not available. "
                "Install with: pip install 'pipecat[openai-realtime]'"
            )
            return None

        try:
            # Use assistant_prompt if provided, otherwise fallback to system_prompt from config
            instructions = assistant_prompt or self.config.get(
                "system_prompt",
                """
                You are a helpful and friendly AI assistant.

                You are participating in a voice conversation. Keep your responses concise, short, and to the point
                unless specifically asked to elaborate on a topic.

                Remember, your responses should be short. Just one or two sentences, usually.""",
            )
            # instructions = """Personality/affect: a high-energy cheerleader helping with administrative tasks \n\nVoice: Enthusiastic, and bubbly, with an uplifting and motivational quality.\n\nTone: Encouraging and playful, making even simple tasks feel exciting and fun.\n\nDialect: Casual and upbeat, using informal phrasing and pep talk-style expressions.\n\nPronunciation: Crisp and lively, with exaggerated emphasis on positive words to keep the energy high.\n\nFeatures: Uses motivational phrases, cheerful exclamations, and an energetic rhythm to create a sense of excitement and engagement."""

            # Get voice configuration
            tts_cfg = self.tts_config
            llm_cfg = self.llm_config
            voice = tts_cfg.voice or "alloy"
            # OpenAI voices: alloy, ash, ballad, coral, echo, sage, shimmer, and verse

            if voice not in [
                "alloy",
                "ash",
                "ballad",
                "coral",
                "echo",
                "sage",
                "shimmer",
                "verse",
            ]:
                self._logger.warning(
                    f"Invalid OpenAI Realtime voice '{voice}', defaulting to 'alloy'"
                )
                voice = os.getenv("OPENAI_REALTIME_TTS_VOICE", "sage")

            # Get model configuration
            model = llm_cfg.model or "gpt-realtime-mini"
            if model not in ["gpt-realtime-mini", "gpt-realtime"]:
                self._logger.warning(
                    f"Invalid Realtime model '{model}', defaulting to 'gpt-realtime-mini'"
                )
                model = "gpt-realtime-mini"

            session_properties, tools = self.get_openai_realtime_settings(
                instructions, model, voice
            )

            use_azure_for_openai = (
                os.getenv("USE_AZURE_FOR_REALTIME", "false").lower() == "true"
            )
            if use_azure_for_openai:
                from pipecat.services.azure.realtime.llm import AzureRealtimeLLMService

                self._logger.info("Using Azure OpenAI endpoint for OpenAI Realtime")
                llm_service = AzureRealtimeLLMService(
                    api_key=os.getenv("AZURE_IN_API_KEY"),
                    base_url=os.getenv("AZURE_REALTIME_ENDPOINT"),
                    session_properties=session_properties,
                    start_audio_paused=False,
                )
            else:
                self._logger.info("Using standard OpenAI endpoint for OpenAI Realtime")
                # Create the service
                llm_service = OpenAIRealtimeLLMService(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    session_properties=session_properties,
                    start_audio_paused=False,
                )

            self._logger.info("✓ OpenAI Realtime LLM service created successfully")
            return llm_service

        except Exception as e:
            self._logger.error(f"Failed to create OpenAI Realtime LLM service: {e}")
            import traceback

            self._logger.error(f"Traceback:\n{traceback.format_exc()}")
            return None

    def get_openai_realtime_settings(self, instructions, model, voice):
        # Get turn detection mode
        turn_detection_enabled = self.config.get("turn_detection", True)
        # Configure audio settings
        audio_config = AudioConfiguration(
            input=AudioInput(
                transcription=InputAudioTranscription(),
                turn_detection=SemanticTurnDetection()
                if turn_detection_enabled
                else False,
                noise_reduction=InputAudioNoiseReduction(type="near_field"),
            ),
            output=AudioOutput(
                voice=voice,
            ),
        )
        # Build tools list using ToolsManager
        tools_manager = ToolsManager(self.config)
        function_schemas = tools_manager.build_function_schemas()
        # Convert FunctionSchema objects to OpenAI Realtime API format
        # OpenAI Realtime expects: {"type": "function", "name": "...", "description": "...", "parameters": {...}}
        tools = []
        for schema in function_schemas:
            tool_dict = schema.to_default_dict()
            tool_dict["type"] = "function"  # Add type field at same level as name
            tools.append(tool_dict)

        self._logger.info(
            f"Creating OpenAI Realtime LLM - model: {model}, voice: {voice}, "
            f"turn_detection: {turn_detection_enabled}"
        )
        # Create session properties
        # NOTE: Do NOT set 'id' - it's generated by the server, not provided by client
        session_config = {
            "audio": audio_config,
            "instructions": instructions,
            "model": model,
            "tool_choice": "auto" if self.tool_calling else "none",
        }
        # Mixed mode: Force text output for separate TTS
        # Full realtime: Let default to audio (don't pass output_modalities)
        if self.mixed_realtime_mode:
            session_config["output_modalities"] = ["text"]
            self._logger.info(
                "🔀 Mixed mode: output_modalities=['text'] for separate TTS"
            )
        else:
            self._logger.info(
                "⚡ Full realtime: output_modalities defaults to ['audio']"
            )
        # Add tools if available
        if tools:
            session_config["tools"] = tools
            self._logger.info(f"✓ Registered {len(tools)} tools for OpenAI Realtime")
        session_properties = SessionProperties(**session_config)
        return session_properties, tools

    def _create_gemini_live_llm_service(
        self, assistant_prompt: Optional[str] = None
    ) -> Optional[Any]:
        """
        Create Gemini Live Vertex LLM service with audio configuration.

        Gemini Live provides:
        - Native audio input/output (no separate STT/TTS needed)
        - Lower latency (end-to-end voice)
        - Function calling support
        - Multiple voice options: Aoede, Charon, Fenrir, Kore, Puck

        Args:
            assistant_prompt: Full prompt from prompt_manager (system instruction)

        Returns:
            GeminiLiveVertexLLMService instance or None on failure
        """
        if not GEMINI_LIVE_AVAILABLE:
            self._logger.error(
                "Gemini Live API not available. "
                "Install with: pip install 'pipecat[google]'"
            )
            return None

        try:
            # Use assistant_prompt if provided, otherwise fallback to system_prompt from config
            instructions = assistant_prompt or self.config.get(
                "system_prompt",
                """
                You are a helpful and friendly AI assistant.

                You are participating in a voice conversation. Keep your responses concise, short, and to the point
                unless specifically asked to elaborate on a topic.

                Remember, your responses should be short. Just one or two sentences, usually.""",
            )

            # Get voice configuration
            # Gemini Live voices: Puck, Charon, Kore, Fenrir, Aoede, Leda, Orus, Zephyr
            tts_cfg = self.tts_config
            llm_cfg = self.llm_config
            voice = tts_cfg.voice or "Puck"

            # Validate voice using constants
            if voice not in GEMINI_REALTIME_VOICES:
                self._logger.warning(
                    f"Invalid Gemini Live voice '{voice}', defaulting to 'Puck'. "
                    f"Valid voices: {', '.join(GEMINI_REALTIME_VOICES)}"
                )
                voice = "Puck"

            # Get credentials configuration
            credentials = self.config.get(
                "google_credentials", os.getenv("GOOGLE_CREDENTIALS")
            )
            project_id = self.config.get(
                "google_project_id", os.getenv("GOOGLE_CLOUD_PROJECT_ID")
            )
            location = self.config.get(
                "google_location", os.getenv("GOOGLE_CLOUD_LOCATION", "asia-south1")
            )

            if not credentials or not project_id:
                self._logger.error(
                    "Gemini Live requires google_credentials and google_project_id. "
                    "Set via config or env vars: GOOGLE_VERTEX_TEST_CREDENTIALS, GOOGLE_CLOUD_PROJECT_ID"
                )
                return None

            # Get model configuration
            # Valid models: gemini-2.5-flash, gemini-2.0-flash-live-001, gemini-2.0-flash-exp
            model = llm_cfg.model or "gemini-2.5-flash"

            # Validate model using constants
            if model not in GEMINI_REALTIME_MODELS:
                self._logger.warning(
                    f"Invalid Gemini Live model '{model}', defaulting to 'gemini-2.5-flash'. "
                    f"Valid models: {', '.join(GEMINI_REALTIME_MODELS)}"
                )
                model = "gemini-2.5-flash"

            self._logger.info(
                f"Creating Gemini Live Vertex LLM - model: {model}, voice: {voice}, "
                f"project: {project_id}, location: {location}"
            )

            # Get Gemini Live-specific settings
            params, tools = self.get_gemini_realtime_settings(
                instructions, model, voice
            )

            # Create the service
            # Gemini Live uses InputParams with modalities parameter
            # - Mixed mode: modalities=TEXT for separate TTS
            # - Full realtime: modalities=AUDIO for integrated audio
            llm_service = GeminiLiveVertexLLMService(
                credentials_path=credentials,
                project_id=project_id,
                location=location,
                system_instruction=instructions,
                start_audio_paused=True,
                start_video_paused=True,
                # params=params,
                model=model,
                voice_id=voice,
                # tools=tools,
            )

            self._logger.info("✓ Gemini Live Vertex LLM service created successfully")
            return llm_service

        except Exception as e:
            self._logger.error(f"Failed to create Gemini Live LLM service: {e}")
            import traceback

            self._logger.error(f"Traceback:\n{traceback.format_exc()}")
            return None

    def get_gemini_realtime_settings(self, instructions, model, voice):
        """
        Build Gemini Live-specific configuration parameters.

        Returns:
            Tuple of (InputParams or None, tools list)
        """
        try:
            from pipecat.services.google.gemini_live.llm_vertex import InputParams
            from pipecat.transcriptions.language import Language

            # Build tools list using ToolsManager
            tools_manager = ToolsManager(self.config)
            function_schemas = tools_manager.build_function_schemas()

            # Gemini Live uses FunctionSchema format directly (same as pipecat)
            tools = function_schemas if self.tool_calling else []

            # Get voice-optimized parameters
            temperature = self.config.get("temperature", 0.4)
            max_tokens = self.config.get("max_tokens", 4096)

            # Determine modalities based on mode
            # Mixed mode: TEXT output for separate TTS
            # Full realtime: AUDIO output (integrated TTS)
            if self.mixed_realtime_mode:
                from pipecat.services.google.gemini_live.llm_vertex import (
                    GeminiModalities,
                )

                modalities = GeminiModalities.TEXT
                self._logger.info("🔀 Mixed mode: modalities=TEXT for separate TTS")
            else:
                from pipecat.services.google.gemini_live.llm_vertex import (
                    GeminiModalities,
                )

                modalities = GeminiModalities.AUDIO
                self._logger.info(
                    "⚡ Full realtime: modalities=AUDIO (integrated audio)"
                )

            # Get language configuration
            language_code = self.config.get("language", "en")
            # Map language codes to Gemini Language enum
            language_map = {
                "en": Language.EN_IN,
                "en-us": Language.EN_US,
                "en-in": Language.EN_IN,
                "hi": Language.HI,
                "pa": Language.PA,
                "ta": Language.TA,
            }
            language = language_map.get(language_code.lower(), Language.EN_IN)

            # Create InputParams for Gemini Live
            params = InputParams(
                temperature=temperature,
                max_tokens=max_tokens,
                modalities=modalities,
                language=language,
            )

            self._logger.info(
                f"Creating Gemini Live - model: {model}, voice: {voice}, "
                f"temperature: {temperature}, max_tokens: {max_tokens}"
            )

            # Log tools
            if tools:
                self._logger.info(f"✓ Registered {len(tools)} tools for Gemini Live")

            return params, tools

        except ImportError:
            self._logger.warning(
                "Gemini Live InputParams not available, returning None"
            )
            # Build tools anyway
            tools_manager = ToolsManager(self.config)
            function_schemas = tools_manager.build_function_schemas()
            tools = function_schemas if self.tool_calling else []
            return None, tools

    async def _create_llm_service_with_retry(
        self, assistant_prompt: Optional[str] = None
    ) -> Optional[Any]:
        """
        Create LLM service with exponential backoff retry logic.

        Retry strategy:
        - Attempts: 1 for startup (configurable via LLM_RETRY_ATTEMPTS env or config)
        - Backoff: Fast (0.5s, 1s) for startup optimization
        - Rate limits: Extended backoff (1s, 2s)
        - Fallback: OpenAI GPT-4o-mini if all attempts fail

        Handles:
        - Transient network errors
        - API rate limits (429)
        - Service unavailability
        - Timeout errors

        Args:
            assistant_prompt: Optional assistant prompt for Realtime API

        Returns:
            LLM service instance or None if all attempts + fallback fail
        """
        import asyncio

        # Check if assistant_prompt was set as instance variable (for backward compatibility)
        if assistant_prompt is None and hasattr(self, "_assistant_prompt"):
            assistant_prompt = self._assistant_prompt

        # Prioritize env var > config > default (1 for fast startup)
        max_retries = int(
            os.getenv("LLM_RETRY_ATTEMPTS", self.config.get("llm_retry_attempts", 2))
        )
        backoff_multiplier = float(
            os.getenv("LLM_RETRY_BACKOFF", self.config.get("llm_retry_backoff", 0.5))
        )
        service_timeout = float(
            os.getenv("LLM_SERVICE_TIMEOUT", "5.0")
        )  # 5s timeout per attempt
        skip_fallback = (
            os.getenv("SKIP_SERVICE_FALLBACK_ON_STARTUP", "false").lower() == "true"
        )

        for attempt in range(1, max_retries + 1):
            try:
                # Direct call (service creation is already fast, timeout handled by underlying APIs)
                service = self._create_llm_service(assistant_prompt)

                if service:
                    if attempt > 1:
                        self._logger.info(
                            f"LLM service created successfully on attempt {attempt}/{max_retries}"
                        )
                    return service

                self._logger.warning(
                    f"LLM service creation returned None (attempt {attempt}/{max_retries})"
                )

            except Exception as e:
                error_msg = str(e)
                self._logger.error(
                    f"LLM service creation failed (attempt {attempt}/{max_retries}): {error_msg}",
                    exc_info=(
                        attempt == max_retries
                    ),  # Full stack trace on last attempt
                )

                # Check if rate limit error (429 or "rate" in message)
                if "rate" in error_msg.lower() or "429" in error_msg:
                    # Rate limit: fast backoff for startup (1s, 2s with default 0.5 multiplier)
                    wait_time = (backoff_multiplier**attempt) * 2
                    self._logger.warning(
                        f"Rate limit detected (429), waiting {wait_time}s before retry {attempt + 1}/{max_retries}"
                    )
                    if attempt < max_retries:
                        await asyncio.sleep(
                            wait_time
                        )  # ✅ FIXED: Non-blocking async sleep
                elif attempt < max_retries:
                    # Other error: fast exponential backoff (0.5s, 1s with default 0.5 multiplier)
                    wait_time = backoff_multiplier**attempt
                    self._logger.info(
                        f"Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(wait_time)  # ✅ FIXED: Non-blocking async sleep

        # All retries failed: try fallback provider (unless disabled for fast startup)
        if skip_fallback:
            self._logger.warning(
                f"All {max_retries} LLM creation attempts failed for provider '{self.config.get('llm_provider')}', "
                "skipping fallback (SKIP_SERVICE_FALLBACK_ON_STARTUP=true)"
            )
            return None

        self._logger.error(
            f"All {max_retries} LLM creation attempts failed for provider '{self.config.get('llm_provider')}', "
            "attempting fallback provider"
        )
        fallback = self._create_llm_from_fallback_chain(assistant_prompt)
        if fallback:
            return fallback
        return self._create_fallback_llm()

    def _create_llm_service(
        self, assistant_prompt: Optional[str] = None
    ) -> Optional[Any]:
        """
        Create LLM service based on config.

        Supports providers:
        - gemini: Google Gemini Multimodal Live
        - anthropic: Anthropic Claude models
        - azure: Azure OpenAI Service
        - openai: OpenAI GPT models (including Realtime API)
        - groq: Groq LLM service
        - google: Google Vertex AI
        - aws: AWS Bedrock

        Args:
            assistant_prompt: Optional assistant prompt for Realtime API

        Returns:
            Configured LLM service instance or None on failure
        """
        cfg = self.llm_config
        provider_normalized = cfg.provider.lower()
        use_inference = self._common.should_use_inference("llm")

        if self.use_realtime and provider_normalized == "openai":
            self._logger.info("Using OpenAI Realtime API mode")
            return self._create_openai_realtime_llm_service(assistant_prompt)

        if self.use_realtime and provider_normalized == "google":
            self._logger.info("Using Gemini Live Vertex API mode")
            return self._create_gemini_live_llm_service(assistant_prompt)

        # Route ALL inference-supported providers through LiveKit gateway
        if use_inference:
            self._logger.info(
                f"LLM inference mode: {provider_normalized}/{cfg.model}"
            )
            return self._create_inference_llm()

        self._logger.info(
            f"LLM provider: {cfg.provider}, llm_model: {cfg.model}"
        )

        max_tokens = self._get_voice_optimized_max_tokens()
        temperature = self._get_voice_optimized_temperature()
        cache_key = self._build_cache_key()

        try:
            creators = {
                "gemini": lambda: self._create_gemini_multimodal_llm(),
                "anthropic": lambda: self._create_anthropic_llm(
                    temperature, max_tokens, cache_key
                ),
                "azure": lambda: self._create_azure_llm(temperature, max_tokens),
                "openai": lambda: self._create_openai_llm(
                    temperature, max_tokens, cache_key
                ),
                "groq": lambda: self._create_groq_llm(temperature, max_tokens),
                "cerebras": lambda: self._create_cerebras_llm(temperature, max_tokens),
                "ollama": lambda: self._create_ollama_llm(temperature, max_tokens),
                "google": lambda: self._create_google_vertex_llm(
                    temperature, max_tokens
                ),
                "aws": lambda: self._create_aws_bedrock_llm(temperature, max_tokens),
            }

            creator = creators.get(provider_normalized)
            if creator:
                return creator()

            from pipecat.services.openai.llm import OpenAILLMService

            return OpenAILLMService(model="gpt-4o-mini")

        except Exception as e:
            self._logger.error(f"Failed to create LLM service: {e}")
            return None

    def _register_docs_if_needed(self, llm_service: Any) -> None:
        if self.tool_calling and self.get_docs_callback:
            llm_service.register_function(
                "get_knowledge_base_info", self.get_docs_callback
            )

    def _create_gemini_multimodal_llm(self) -> Optional[Any]:
        from pipecat.services.gemini_multimodal_live import (
            GeminiMultimodalLiveLLMService,
        )

        tts_cfg = self.tts_config
        gemini_voice = tts_cfg.voice or "Puck"
        if gemini_voice not in GEMINI_REALTIME_VOICES:
            self._logger.warning(
                f"Invalid Gemini voice '{gemini_voice}', using 'Puck'. "
                f"Valid voices: {', '.join(GEMINI_REALTIME_VOICES)}"
            )
            gemini_voice = "Puck"

        return GeminiMultimodalLiveLLMService(
            api_key=os.getenv("GOOGLE_API_KEY"),
            voice_id=gemini_voice,
            transcribe_model_audio=True,
            system_instruction=self.config.get("system_prompt"),
        )

    def _create_anthropic_llm(
        self, temperature: float, max_tokens: int, cache_key: str
    ) -> Optional[Any]:
        from pipecat.services.anthropic.llm import AnthropicLLMService

        cfg = self.llm_config
        return AnthropicLLMService(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model=cfg.model or "claude-sonnet-4-20250514",
            params=AnthropicLLMService.InputParams(
                temperature=temperature,
                enable_prompt_caching=True,
                max_completion_tokens=max_tokens,
                prompt_cache_key=cache_key,
            ),
        )

    def _create_azure_llm(
        self, temperature: float, max_tokens: int
    ) -> Optional[Any]:
        from pipecat.services.azure.llm import AzureLLMService

        cfg = self.llm_config
        return AzureLLMService(
            api_key=os.getenv("AZURE_IN_API_KEY"),
            endpoint=self.config.get("endpoint", os.getenv("AZURE_BASE_URL")),
            model=cfg.model or os.getenv("AZURE_CHATGPT_MODEL"),
            params=AzureLLMService.InputParams(
                temperature=temperature,
                max_completion_tokens=max_tokens,
            ),
        )

    def _create_openai_llm(
        self,
        temperature: float,
        max_tokens: int,
        cache_key: str,
    ) -> Optional[Any]:
        from pipecat.services.openai.llm import OpenAILLMService

        cfg = self.llm_config
        params = OpenAILLMService.InputParams(
            temperature=temperature,
            max_completion_tokens=max_tokens,
            extra={
                "prompt_cache_key": cache_key,
            },
        )

        return OpenAILLMService(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=cfg.model or "gpt-4o",
            params=params,
        )

    def _create_inference_llm(self) -> Optional[Any]:
        """Create LLM via LiveKit inference gateway (works for all supported providers)."""
        from pipecat.services.openai.llm import OpenAILLMService

        max_tokens = self._get_voice_optimized_max_tokens()
        temperature = self._get_voice_optimized_temperature()
        cache_key = self._build_cache_key()

        base_url, api_key, model_ref = self._common.get_inference_credentials("llm")

        params = OpenAILLMService.InputParams(
            temperature=temperature,
            max_completion_tokens=max_tokens,
            extra={"prompt_cache_key": cache_key},
        )

        self._logger.info(f"Creating inference LLM: {model_ref} via {base_url}")

        model= self.config.get("llm_model")
        return OpenAILLMService(
            api_key=api_key,
            base_url=base_url,
            model=model,
            params=params,
        )

    def _create_groq_llm(
        self, temperature: float, max_tokens: int
    ) -> Optional[Any]:
        from pipecat.services.groq.llm import GroqLLMService

        cfg = self.llm_config
        model = cfg.model or "llama-3.3-70b-versatile"
        extra = {}
        if model.startswith("qwen/qwen3-32b"):
            extra["reasoning_effort"] = "none"
        llm_service = GroqLLMService(
            api_key=os.getenv("GROQ_API_KEY"),
            model=model,
            params=GroqLLMService.InputParams(
                temperature=temperature,
                max_completion_tokens=max_tokens,
                extra=extra,
            ),
        )
        self._register_docs_if_needed(llm_service)
        return llm_service

    def _create_cerebras_llm(
        self, temperature: float, max_tokens: int
    ) -> Optional[Any]:
        from pipecat.services.cerebras.llm import CerebrasLLMService
        from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext

        cfg = self.llm_config
        model = cfg.model or "qwen3-32b"
        context_limit = get_model_context_limit(model)

        # Create a subclass with context truncation for small context models
        class ContextAwareCerebrasLLMService(CerebrasLLMService):
            """Cerebras LLM service with automatic context truncation."""

            def __init__(self, *args, context_limit: int = 8192, max_tokens: int = 500, **kwargs):
                super().__init__(*args, **kwargs)
                self._context_limit = context_limit
                self._max_tokens = max_tokens
                self._effective_limit = context_limit - max_tokens - 200

            async def _stream_chat_completions_specific_context(self, context: OpenAILLMContext):
                """Override to truncate context before sending to LLM."""
                messages = context.get_messages()
                messages = self._truncate_messages(messages)
                # Update context with truncated messages
                context.set_messages(messages)
                return await super()._stream_chat_completions_specific_context(context)

            def _truncate_messages(self, messages: list) -> list:
                """Truncate messages to fit within context limit."""
                if not messages:
                    return messages

                # Calculate total tokens
                total_tokens = sum(
                    estimate_tokens(str(m.get("content", ""))) for m in messages
                )

                if total_tokens <= self._effective_limit:
                    return messages

                # Separate system messages from conversation
                sys_msgs = [m for m in messages if m.get("role") == "system"]
                conv_msgs = [m for m in messages if m.get("role") in ("user", "assistant")]

                # Calculate system tokens
                sys_tokens = sum(estimate_tokens(str(m.get("content", ""))) for m in sys_msgs)

                # If system alone exceeds 60% of limit, truncate it
                if sys_tokens > self._effective_limit * 0.6 and sys_msgs:
                    target_chars = int(self._effective_limit * 0.5 * 4)
                    sys_content = str(sys_msgs[-1].get("content", ""))
                    sys_msgs[-1]["content"] = sys_content[:target_chars] + "\n[...truncated...]"
                    sys_tokens = estimate_tokens(sys_msgs[-1]["content"])

                # Keep only most recent system message
                sys_msgs = sys_msgs[-1:] if sys_msgs else []

                # Calculate remaining budget for conversation
                conv_budget = self._effective_limit - sys_tokens - 100

                # Remove oldest conversation messages until within budget
                while conv_msgs and sum(
                    estimate_tokens(str(m.get("content", ""))) for m in conv_msgs
                ) > conv_budget:
                    conv_msgs.pop(0)

                return sys_msgs + conv_msgs

        llm_service = ContextAwareCerebrasLLMService(
            api_key=os.getenv("CEREBRAS_API_KEY"),
            model=model,
            context_limit=context_limit,
            max_tokens=max_tokens,
            params=CerebrasLLMService.InputParams(
                temperature=temperature,
                max_completion_tokens=max_tokens,
            ),
        )
        self._logger.info(
            f"Created Cerebras LLM with context truncation "
            f"(limit={context_limit}, effective={context_limit - max_tokens - 200})"
        )
        self._register_docs_if_needed(llm_service)
        return llm_service

    def _create_ollama_llm(
        self, temperature: float, max_tokens: int
    ) -> Optional[Any]:
        from pipecat.services.ollama.llm import OLLamaLLMService

        cfg = self.llm_config
        llm_service = OLLamaLLMService(
            model=cfg.model or "llama3.2",
            base_url=self.config.get("llm_url", "http://localhost:11434"),
            params=OLLamaLLMService.InputParams(
                temperature=temperature,
                max_completion_tokens=max_tokens,
            ),
        )
        self._register_docs_if_needed(llm_service)
        return llm_service

    def _create_google_vertex_llm(
        self, temperature: float, max_tokens: int
    ) -> Optional[Any]:
        from pipecat.services.google.llm_vertex import GoogleVertexLLMService

        cfg = self.llm_config
        llm_service = GoogleVertexLLMService(
            credentials_path=os.getenv("GOOGLE_CREDENTIALS"),
            model=cfg.model or "google/gemini-2.0-flash-001",
            params=GoogleVertexLLMService.InputParams(
                project_id="unpod-ai",
                location=self.config.get("region", "us-east4"),
                max_completion_tokens=max_tokens,
                temperature=temperature,
            ),
        )
        self._register_docs_if_needed(llm_service)
        return llm_service

    def _create_aws_bedrock_llm(
        self, temperature: float, max_tokens: int
    ) -> Optional[Any]:
        from pipecat.services.aws.llm import AWSBedrockLLMService

        cfg = self.llm_config
        llm_service = AWSBedrockLLMService(
            aws_region=self.config.get("region", "ap-south-1"),
            model=cfg.model or "anthropic.claude-sonnet-4-20250514-v1:0",
            params=AWSBedrockLLMService.InputParams(
                temperature=temperature,
                max_completion_tokens=max_tokens,
            ),
        )
        self._register_docs_if_needed(llm_service)
        return llm_service

    def _stt_or_fallback(self, service: Optional[Any], provider: str) -> Optional[Any]:
        if service:
            return service
        self._logger.warning(
            f"STT provider '{provider}' unavailable, using fallback OpenAI Whisper"
        )
        return self._create_fallback_stt()

    async def _create_stt_service_with_retry(self, context: str = "") -> Optional[Any]:
        """
        Create STT service with exponential backoff retry logic.

        Retry strategy:
        - Attempts: 1 for startup (configurable via STT_RETRY_ATTEMPTS env or config)
        - Backoff: Fast (0.5s, 1s) for startup optimization
        - Fallback: OpenAI Whisper if all attempts fail

        Handles:
        - Transient network errors
        - API rate limits
        - Service unavailability
        - Timeout errors

        Returns:
            STT service instance or None if all attempts + fallback fail
        """
        import asyncio

        # Prioritize env var > config > default (1 for fast startup)
        max_retries = int(
            os.getenv("STT_RETRY_ATTEMPTS", self.config.get("stt_retry_attempts", 2))
        )
        backoff_multiplier = float(
            os.getenv("STT_RETRY_BACKOFF", self.config.get("stt_retry_backoff", 0.5))
        )
        skip_fallback = (
            os.getenv("SKIP_SERVICE_FALLBACK_ON_STARTUP", "false").lower() == "true"
        )

        for attempt in range(1, max_retries + 1):
            try:
                service = self._create_stt_service(context)
                if service:
                    if attempt > 1:
                        self._logger.info(
                            f"STT service created successfully on attempt {attempt}/{max_retries}"
                        )
                    return service

                self._logger.warning(
                    f"STT service creation returned None (attempt {attempt}/{max_retries})"
                )

            except Exception as e:
                error_msg = str(e)
                self._logger.error(
                    f"STT service creation failed (attempt {attempt}/{max_retries}): {error_msg}",
                    exc_info=(
                        attempt == max_retries
                    ),  # Full stack trace on last attempt
                )

                if attempt < max_retries:
                    # Fast exponential backoff for startup (0.5s with default 0.5 multiplier)
                    wait_time = backoff_multiplier**attempt
                    self._logger.info(
                        f"Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(wait_time)

        # All retries failed: try fallback provider (unless disabled for fast startup)
        if skip_fallback:
            self._logger.warning(
                f"All {max_retries} STT creation attempts failed for provider '{self.config.get('stt_provider')}', "
                "skipping fallback (SKIP_SERVICE_FALLBACK_ON_STARTUP=true)"
            )
            return None

        self._logger.error(
            f"All {max_retries} STT creation attempts failed for provider '{self.config.get('stt_provider')}', "
            "attempting fallback provider"
        )
        fallback = self._create_stt_from_fallback_chain(context)
        if fallback:
            return fallback
        return self._create_fallback_stt()

    def _create_stt_service(self, context: str = "") -> Optional[Any]:
        """
        Create STT (Speech-to-Text) service based on config.

        Supports providers:
        - openai: OpenAI Whisper
        - assemblyai: AssemblyAI STT
        - aws: AWS Transcribe STT
        - azure: Azure Speech Services
        - cartesia: Cartesia STT
        - deepgram: Deepgram Nova and Flux models
        - elevenlabs: ElevenLabs STT
        - fal: Fal STT
        - gladia: Gladia STT with custom vocabulary
        - google: Google Cloud Speech-to-Text
        - groq: Groq Whisper STT
        - riva: NVIDIA Riva STT
        - sambanova: SambaNova Whisper STT
        - sarvam: Sarvam STT (if available)
        - soniox: Soniox STT
        - speechmatics: Speechmatics STT
        - ultravox: Ultravox STT
        - whisper: Local Whisper STT

        Args:
            context: Optional context string for improved transcription accuracy

        Returns:
            Configured STT service instance or None on failure
        """
        cfg = self.stt_config
        provider_aliases = {
            "eleven_labs": "elevenlabs",
            "speechmatics-rt": "speechmatics",
            "aws-transcribe": "aws",
            "openai-whisper": "openai",
        }
        provider_normalized = provider_aliases.get(cfg.provider.lower(), cfg.provider.lower())

        try:
            from pipecat.transcriptions.language import Language

            transcribing_languages = [Language.EN, Language.HI]
            user_language = self.get_language(cfg.language or "en")
            if user_language and user_language not in transcribing_languages:
                transcribing_languages.append(user_language)

            creators = {
                "openai": lambda: self._create_openai_stt(user_language),
                "assemblyai": lambda: self._create_assemblyai_stt(user_language),
                "aws": lambda: self._create_aws_stt(user_language),
                "azure": lambda: self._create_azure_stt(user_language),
                "cartesia": self._create_cartesia_stt,
                "deepgram": self._create_deepgram_stt,
                "elevenlabs": lambda: self._create_elevenlabs_stt(user_language),
                "fal": self._create_fal_stt,
                "gladia": lambda: self._create_gladia_stt(user_language),
                "google": lambda: self._create_google_stt(transcribing_languages),
                "groq": lambda: self._create_groq_stt(user_language),
                "riva": lambda: self._create_riva_stt(user_language),
                "sambanova": lambda: self._create_sambanova_stt(user_language),
                "sarvam": lambda: self._create_sarvam_stt(user_language),
                "soniox": lambda: self._create_soniox_stt(
                    transcribing_languages, context
                ),
                "speechmatics": lambda: self._create_speechmatics_stt(user_language),
                "ultravox": self._create_ultravox_stt,
                "whisper": lambda: self._create_whisper_stt(user_language),
            }

            creator = creators.get(provider_normalized)
            if creator:
                return self._stt_or_fallback(creator(), provider_normalized)

            return self._create_openai_stt(user_language)

        except Exception as e:
            self._logger.error(f"Failed to create STT service: {e}")
            return None

    def _create_openai_stt(self, user_language: Any) -> Optional[Any]:
        from pipecat.services.openai.stt import OpenAISTTService
        from pipecat.transcriptions.language import Language

        cfg = self.stt_config
        primary_language = user_language or Language.EN
        model = cfg.model or "whisper-1"

        self._logger.info(
            f"OpenAI STT configured - language: {primary_language}, model: {model}"
        )
        self._logger.warning(
            "OpenAI Whisper STT does not support interim results. "
            "Consider using Deepgram for real-time transcription feedback. "
            "Users may experience 1-3 second delay before transcripts appear."
        )

        return OpenAISTTService(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=model,
            language=primary_language,
        )

    def _create_cartesia_stt(self) -> Optional[Any]:
        from pipecat.services.cartesia.stt import CartesiaSTTService

        return CartesiaSTTService(api_key=os.getenv("CARTESIA_API_KEY"))

    def _create_fal_stt(self) -> Optional[Any]:
        from pipecat.services.fal.stt import FalSTTService

        return FalSTTService(api_key=os.getenv("FAL_KEY"))

    def _create_gladia_stt(self, user_language: Any) -> Optional[Any]:
        from pipecat.services.gladia.stt import GladiaSTTService
        from pipecat.services.gladia.config import (
            CustomVocabularyConfig,
            CustomVocabularyItem,
            RealtimeProcessingConfig,
            LanguageConfig,
        )
        from pipecat.services.gladia.stt import GladiaInputParams
        from pipecat.transcriptions.language import Language

        custom_vocab_list = self.config.get("custom_vocabulary", [])

        vocab = None
        if custom_vocab_list:
            vocab_items = []
            for term in custom_vocab_list:
                if isinstance(term, str):
                    vocab_items.append(
                        CustomVocabularyItem(value=term, intensity=0.8)
                    )
                elif isinstance(term, dict):
                    vocab_items.append(
                        CustomVocabularyItem(
                            value=term.get("value"),
                            intensity=term.get("intensity", 0.8),
                        )
                    )

            vocab = CustomVocabularyConfig(
                vocabulary=vocab_items, default_intensity=0.6
            )

            self._logger.info(
                f"Gladia STT custom vocabulary: {len(vocab_items)} terms loaded"
            )
        else:
            self._logger.info(
                "Gladia STT: No custom vocabulary configured (use 'custom_vocabulary' in config)"
            )

        cfg = self.stt_config
        return GladiaSTTService(
            api_key=os.getenv("GLADIA_API_KEY"),
            model=cfg.model or "solaria-1",
            params=GladiaInputParams(
                language_config=LanguageConfig(
                    languages=[Language.EN, Language.HI, user_language],
                    code_switching=True,
                ),
                realtime_processing=RealtimeProcessingConfig(
                    custom_vocabulary=bool(vocab),
                    custom_vocabulary_config=vocab,
                ),
            ),
        )

    def _create_deepgram_stt(self) -> Optional[Any]:
        from pipecat.services.deepgram.stt import (
            DeepgramSTTService,
            LiveOptions,
        )

        cfg = self.stt_config
        model_name = cfg.model or "nova-3"
        use_finals_only = self.config.get("use_final_transcriptions_only", False)

        if model_name.startswith("flux"):
            from pipecat.services.deepgram.flux.stt import (
                DeepgramFluxSTTService,
            )

            params = DeepgramFluxSTTService.InputParams(
                eager_eot_threshold=0.5,
                eot_threshold=0.8,
                keyterm=["AI", "machine learning", "neural network"],
                tag=["production", "voice-agent"],
            )
            return DeepgramFluxSTTService(
                api_key=os.getenv("DEEPGRAM_API_KEY"),
                model=model_name,
                params=params,
            )

        if use_finals_only:
            self._logger.info(
                "Deepgram STT: Using final transcriptions only (interim_results=False)"
            )

        return DeepgramSTTService(
            api_key=os.getenv("DEEPGRAM_API_KEY"),
            live_options=LiveOptions(
                model=model_name,
                language="multi",
                smart_format=True,
                interim_results=not use_finals_only,
                punctuate=True,
                profanity_filter=True,
            ),
        )

    def _create_soniox_stt(
        self, transcribing_languages: Any, context: str
    ) -> Optional[Any]:
        from pipecat.services.soniox.stt import (
            SonioxSTTService,
            SonioxInputParams,
        )

        cfg = self.stt_config
        return SonioxSTTService(
            api_key=os.getenv("SONIOX_API_KEY"),
            params=SonioxInputParams(
                model=cfg.model,
                language_hints=transcribing_languages,
                context=context,
            ),
        )

    def _create_google_stt(
        self, transcribing_languages: Any
    ) -> Optional[Any]:
        from pipecat.services.google.stt import GoogleSTTService

        cfg = self.stt_config
        use_finals_only = self.config.get("use_final_transcriptions_only", False)
        if use_finals_only:
            self._logger.info(
                "Google STT: Using final transcriptions only (enable_interim_results=False)"
            )

        return GoogleSTTService(
            credentials_path=os.getenv("GOOGLE_CREDENTIALS"),
            location="global",
            params=GoogleSTTService.InputParams(
                languages=transcribing_languages,
                model=cfg.model,
                enable_automatic_punctuation=True,
                enable_interim_results=not use_finals_only,
            ),
        )

    def _create_azure_stt(self, user_language: Any) -> Optional[Any]:
        from pipecat.services.azure.stt import AzureSTTService

        return AzureSTTService(
            api_key=os.getenv("AZURE_SPEECH_API_KEY"),
            region=os.getenv("AZURE_SPEECH_REGION"),
            language=user_language,
        )

    def _create_sarvam_stt(self, user_language: Any) -> Optional[Any]:
        from pipecat.services.sarvam.stt import SarvamSTTService

        cfg = self.stt_config

        # Map language codes to Sarvam format
        lang_map = {
            "hi": "hi-IN",
            "ta": "ta-IN",
            "te": "te-IN",
            "kn": "kn-IN",
            "ml": "ml-IN",
            "mr": "mr-IN",
            "bn": "bn-IN",
            "gu": "gu-IN",
            "pa": "pa-IN",
            "en": "en-IN",
        }
        target_language = lang_map.get(cfg.language.lower(), "hi-IN")
        model = cfg.model or "saarika:v2.5"

        self._logger.info(
            f"Sarvam STT configured - language: {target_language}, model: {model}"
        )

        return SarvamSTTService(
            api_key=os.getenv("SARVAM_API_KEY"),
            model=model,
            language=target_language,
        )

    def _create_assemblyai_stt(self, user_language: Any) -> Optional[Any]:
        from pipecat.services.assemblyai.stt import AssemblyAISTTService
        from pipecat.transcriptions.language import Language

        return AssemblyAISTTService(
            api_key=os.getenv("ASSEMBLYAI_API_KEY"),
            language=user_language or Language.EN,
        )

    def _create_aws_stt(self, user_language: Any) -> Optional[Any]:
        try:
            from pipecat.services.aws.stt import AWSTranscribeSTTService
        except Exception as exc:  # pragma: no cover - optional dependency
            self._logger.warning(f"AWS STT unavailable: {exc}")
            return None

        return AWSTranscribeSTTService(
            api_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
            region=os.getenv("AWS_REGION", "us-east-1"),
            sample_rate=self.config.get("stt_sample_rate"),
            language=user_language,
        )

    def _create_elevenlabs_stt(self, user_language: Any) -> Optional[Any]:
        try:
            import aiohttp
            from pipecat.services.elevenlabs.stt import ElevenLabsSTTService
        except Exception as exc:  # pragma: no cover - optional dependency
            self._logger.warning(f"ElevenLabs STT unavailable: {exc}")
            return None

        cfg = self.stt_config
        session = aiohttp.ClientSession()
        return ElevenLabsSTTService(
            api_key=os.getenv("ELEVENLABS_API_KEY"),
            aiohttp_session=session,
            model=cfg.model or "scribe_v1",
            params=ElevenLabsSTTService.InputParams(language=user_language),
        )

    def _create_groq_stt(self, user_language: Any) -> Optional[Any]:
        try:
            from pipecat.services.groq.stt import GroqSTTService
        except Exception as exc:  # pragma: no cover - optional dependency
            self._logger.warning(f"Groq STT unavailable: {exc}")
            return None

        cfg = self.stt_config
        return GroqSTTService(
            api_key=os.getenv("GROQ_API_KEY"),
            model=cfg.model or "whisper-large-v3-turbo",
            language=user_language,
        )

    def _create_riva_stt(self, user_language: Any) -> Optional[Any]:
        try:
            from pipecat.services.riva.stt import RivaSTTService
        except Exception as exc:  # pragma: no cover - optional dependency
            self._logger.warning(f"Riva STT unavailable: {exc}")
            return None

        api_key = (
            os.getenv("NVIDIA_API_KEY")
            or os.getenv("NVCF_API_KEY")
            or os.getenv("RIVA_API_KEY")
        )
        server = self.config.get("riva_server", os.getenv("RIVA_SERVER"))
        return RivaSTTService(
            api_key=api_key,
            server=server or "grpc.nvcf.nvidia.com:443",
            params=RivaSTTService.InputParams(language=user_language),
        )

    def _create_sambanova_stt(self, user_language: Any) -> Optional[Any]:
        try:
            from pipecat.services.sambanova.stt import SambaNovaSTTService
        except Exception as exc:  # pragma: no cover - optional dependency
            self._logger.warning(f"SambaNova STT unavailable: {exc}")
            return None

        cfg = self.stt_config
        return SambaNovaSTTService(
            api_key=os.getenv("SAMBANOVA_API_KEY"),
            model=cfg.model or "Whisper-Large-v3",
            language=user_language,
        )

    def _create_speechmatics_stt(self, user_language: Any) -> Optional[Any]:
        try:
            from pipecat.services.speechmatics.stt import SpeechmaticsSTTService
        except Exception as exc:  # pragma: no cover - optional dependency
            self._logger.warning(f"Speechmatics STT unavailable: {exc}")
            return None

        return SpeechmaticsSTTService(
            api_key=os.getenv("SPEECHMATICS_API_KEY"),
            base_url=os.getenv("SPEECHMATICS_RT_URL"),
            params=SpeechmaticsSTTService.InputParams(language=user_language)
            if hasattr(SpeechmaticsSTTService, "InputParams")
            else None,
        )

    def _create_ultravox_stt(self) -> Optional[Any]:
        try:
            from pipecat.services.ultravox.stt import UltravoxSTTService
        except Exception as exc:  # pragma: no cover - optional dependency
            self._logger.warning(f"Ultravox STT unavailable: {exc}")
            return None

        cfg = self.stt_config
        return UltravoxSTTService(
            model_name=cfg.model or "fixie-ai/ultravox-v0_5-llama-3_1-8b",
            hf_token=os.getenv("HF_TOKEN"),
            temperature=self.config.get("ultravox_temperature", 0.7),
            max_tokens=self.config.get("ultravox_max_tokens", 100),
        )

    def _create_whisper_stt(self, user_language: Any) -> Optional[Any]:
        try:
            from pipecat.services.whisper.stt import WhisperSTTService
            from pipecat.transcriptions.language import Language
        except Exception as exc:  # pragma: no cover - optional dependency
            self._logger.warning(f"Whisper STT unavailable: {exc}")
            return None

        cfg = self.stt_config
        return WhisperSTTService(
            model=cfg.model or "distil-medium.en",
            device=self.config.get("whisper_device", "auto"),
            compute_type=self.config.get("whisper_compute_type", "default"),
            language=user_language or Language.EN,
        )

    def _create_cartesia_tts_service(
        self,
        model: str,
        voice_id: str,
        language: str,
        speed: str,
        default_voice_id: str = "95d51f79-c397-46f9-b49a-23763d3eaa2d",
        is_retry: bool = False,
    ) -> Optional[Any]:
        """
        Create CartesiaTTSService with fallback to default voice on invalid voice/model error.

        Args:
            model: Cartesia model name (e.g., "sonic-2")
            voice_id: Voice ID to use
            language: Language code
            speed: Speed value ("slow", "normal", "fast")
            default_voice_id: Default voice ID to fallback to
            is_retry: Whether this is a retry attempt with default voice

        Returns:
            CartesiaTTSService instance or raises exception on failure
        """
        from pipecat.services.cartesia.tts import CartesiaTTSService

        try:
            return CartesiaTTSService(
                api_key=os.getenv("CARTESIA_API_KEY"),
                model=model,
                voice_id=voice_id,
                params=CartesiaTTSService.InputParams(language=language, speed=speed),
            )
        except Exception as e:
            error_msg = str(e).lower()
            # Check if it's an invalid voice/model error (status_code 400)
            is_invalid_error = (
                "invalid voice" in error_msg
                or "invalid model" in error_msg
                or "400" in str(e)
                or "status_code" in error_msg
            )

            # Only retry once with default voice if not already using it
            if is_invalid_error and not is_retry and voice_id != default_voice_id:
                self._logger.warning(
                    f"Cartesia TTS: Invalid voice or model (voice='{voice_id}', model='{model}'). "
                    f"Retrying with default voice '{default_voice_id}'"
                )
                # Recursive call with default voice
                return self._create_cartesia_tts_service(
                    model=model,
                    voice_id=default_voice_id,
                    language=language,
                    speed=speed,
                    default_voice_id=default_voice_id,
                    is_retry=True,
                )
            else:
                # Re-raise if already retried or different error
                if is_retry:
                    self._logger.error(
                        f"Cartesia TTS: Default voice '{default_voice_id}' also failed: {e}"
                    )
                raise

    def _validate_openai_voice(
        self, voice: Optional[str], default: str = "alloy", log_warning: bool = True
    ) -> str:
        """Validate and return a valid OpenAI TTS voice."""
        return self._common.validate_openai_voice(
            voice, default=default, log_warning=log_warning
        )

    def _validate_openai_tts_model(
        self, model: Optional[str], default: str = "gpt-4o-mini-tts"
    ) -> str:
        """Validate and return a valid OpenAI TTS model."""
        return self._common.validate_openai_tts_model(model, default=default)

    def _create_fallback_tts(
        self, user_language: Optional[str] = None
    ) -> Optional[Any]:
        """
        Create fallback TTS service using default provider.

        Used when primary provider fails after retries. Provides:
        - High quality voice synthesis
        - Low latency streaming
        - Multilingual support

        Environment variables:
        - FALLBACK_TTS_MODEL: TTS model (default: from DEFAULT_TTS_MODEL)
        - FALLBACK_TTS_VOICE: Voice ID (default: from DEFAULT_TTS_VOICE)

        Returns:
            Fallback TTS service or None if even fallback fails
        """
        try:
            from livekit.agents import inference

            fallback_model = os.getenv("FALLBACK_TTS_MODEL", DEFAULT_TTS_MODEL)
            fallback_voice_id = os.getenv("FALLBACK_TTS_VOICE", DEFAULT_TTS_VOICE)

            self._logger.warning(
                f"Primary TTS failed, using fallback: {DEFAULT_TTS_PROVIDER} {fallback_model} ({fallback_voice_id})"
            )
            cfg = self.tts_config
            return inference.TTS(
                model=f"{DEFAULT_TTS_PROVIDER}/{fallback_model}",
                voice=fallback_voice_id,
                language=self.get_language(
                    user_language or cfg.language or "en"
                ),
            )
        except Exception as e:
            self._logger.critical(f"Fallback TTS also failed: {e}")
            return None

    async def _create_tts_service_with_retry(
        self, user_language: Optional[str] = None
    ) -> Optional[Any]:
        """
        Create TTS service with exponential backoff retry logic.

        Retry strategy:
        - Attempts: 1 for startup (configurable via TTS_RETRY_ATTEMPTS env or config)
        - Backoff: Fast (0.5s, 1s) for startup optimization
        - Fallback: Cartesia Sonic if all attempts fail

        Handles:
        - Transient network errors
        - API rate limits
        - Service unavailability
        - Timeout errors

        Returns:
            TTS service instance or None if all attempts + fallback fail
        """
        import asyncio

        # Prioritize env var > config > default (1 for fast startup)
        max_retries = int(
            os.getenv("TTS_RETRY_ATTEMPTS", self.config.get("tts_retry_attempts", 2))
        )
        backoff_multiplier = float(
            os.getenv("TTS_RETRY_BACKOFF", self.config.get("tts_retry_backoff", 0.5))
        )
        skip_fallback = (
            os.getenv("SKIP_SERVICE_FALLBACK_ON_STARTUP", "false").lower() == "true"
        )

        for attempt in range(1, max_retries + 1):
            try:
                service = self._create_tts_service(user_language)
                if service:
                    if attempt > 1:
                        self._logger.info(
                            f"TTS service created successfully on attempt {attempt}/{max_retries}"
                        )
                    return service

                self._logger.warning(
                    f"TTS service creation returned None (attempt {attempt}/{max_retries})"
                )

            except Exception as e:
                error_msg = str(e)
                self._logger.error(
                    f"TTS service creation failed (attempt {attempt}/{max_retries}): {error_msg}",
                    exc_info=(
                        attempt == max_retries
                    ),  # Full stack trace on last attempt
                )

                if attempt < max_retries:
                    # Fast exponential backoff for startup (0.5s with default 0.5 multiplier)
                    wait_time = backoff_multiplier**attempt
                    self._logger.info(
                        f"Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(wait_time)

        # All retries failed: try fallback provider (unless disabled for fast startup)
        if skip_fallback:
            self._logger.warning(
                f"All {max_retries} TTS creation attempts failed for provider '{self.config.get('tts_provider')}', "
                "skipping fallback (SKIP_SERVICE_FALLBACK_ON_STARTUP=true)"
            )
            return None

        self._logger.error(
            f"All {max_retries} TTS creation attempts failed for provider '{self.config.get('tts_provider')}', "
            "attempting fallback provider"
        )
        fallback = self._create_tts_from_fallback_chain(user_language)
        if fallback:
            return fallback
        return self._create_fallback_tts(user_language)

    def _create_tts_service(self, user_language: Optional[str] = None) -> Optional[Any]:
        """
        Create TTS (Text-to-Speech) service based on config.

        Supports providers:
        - openai: OpenAI TTS (tts-1, gpt-4o-mini-tts)
        - groq: Groq TTS
        - sarvam: Sarvam TTS (Indian languages)
        - elevenlabs: ElevenLabs TTS
        - deepgram: Deepgram Aura TTS
        - cartesia: Cartesia Sonic TTS
        - google: Google Cloud Text-to-Speech
        - lmnt: LMNT TTS

        Returns:
            Configured TTS service instance or None on failure
        """
        cfg = self.tts_config
        provider_normalized = cfg.provider.lower()
        user_language = user_language or cfg.language or "en"

        try:
            creator = self._get_tts_creator(provider_normalized)
            if creator:
                return creator(user_language)

            self._logger.warning(
                f"Unknown TTS provider '{provider_normalized}', using fallback"
            )
            return self._create_fallback_tts(user_language)

        except Exception as e:
            self._logger.error(f"Failed to create TTS service: {e}")
            return None

    def _get_tts_creator(self, provider: str):
        creators = {
            "openai": self._create_openai_tts,
            "groq": self._create_groq_tts,
            "sarvam": self._create_sarvam_tts,
            "elevenlabs": self._create_elevenlabs_tts,
            "deepgram": self._create_deepgram_tts,
            "cartesia": self._create_cartesia_tts,
            "google": self._create_google_tts,
            "lmnt": self._create_lmnt_tts,
        }
        return creators.get(provider)

    def _create_openai_tts(self, user_language: str) -> Optional[Any]:
        from pipecat.services.openai.tts import OpenAITTSService

        cfg = self.tts_config
        tts_model = self._validate_openai_tts_model(cfg.model)
        voice = self._validate_openai_voice(cfg.voice, default="alloy")

        voice_instructions = self.config.get(
            "voice_instructions",
            "Speak naturally and professionally in a conversational tone.",
        )

        self._logger.info(
            f"OpenAI TTS configured - model: {tts_model}, voice: {voice}"
        )

        if tts_model in ["tts-1", "tts-1-hd"]:
            self._logger.warning(
                f"TTS model '{tts_model}' is legacy. Consider upgrading to "
                "'gpt-4o-mini-tts' or 'gpt-4o-audio-preview' for better quality and voice instructions."
            )
            return OpenAITTSService(
                api_key=os.getenv("OPENAI_API_KEY"),
                model=tts_model,
                voice=voice,
            )

        return OpenAITTSService(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=tts_model,
            voice=voice,
            language=self.get_language(user_language),
            instructions=voice_instructions,
        )

    def _create_groq_tts(self, user_language: str) -> Optional[Any]:
        from pipecat.services.groq.tts import GroqTTSService

        cfg = self.tts_config
        return GroqTTSService(
            api_key=os.getenv("GROQ_API_KEY"),
            voice_id=cfg.voice,
            model_name=cfg.model,
        )

    def _create_sarvam_tts(self, user_language: str) -> Optional[Any]:
        import aiohttp
        from pipecat.services.sarvam.tts import SarvamTTSService

        cfg = self.tts_config
        session = aiohttp.ClientSession()
        return SarvamTTSService(
            api_key=os.getenv("SARVAM_API_KEY"),
            voice_id=cfg.voice,
            aiohttp_session=session,
            params=SarvamTTSService.InputParams(
                language=self.get_language(user_language),
                pitch=self.config.get("pitch", 0.3),
                pace=self.config.get("voice_speed", 1.0),
                loudness=self.config.get("loudness", 1),
            ),
        )

    def _create_elevenlabs_tts(self, user_language: str) -> Optional[Any]:
        from pipecat.services.elevenlabs.tts import ElevenLabsTTSService

        cfg = self.tts_config
        return ElevenLabsTTSService(
            api_key=os.getenv("ELEVENLABS_API_KEY"),
            voice_id=cfg.voice,
            model=cfg.model or "eleven_multilingual_v2",
            params=ElevenLabsTTSService.InputParams(
                language=self.get_language(user_language),
                stability=self.config.get("stability", 0.5),
                similarity_boost=self.config.get("similarity", 0.6),
                style=self.config.get("style", 0.5),
                use_speaker_boost=True,
                speed=self.config.get("tts_speed", 0.95),
            ),
        )

    def _create_deepgram_tts(self, user_language: str) -> Optional[Any]:
        from pipecat.services.deepgram.tts import DeepgramTTSService

        cfg = self.tts_config
        return DeepgramTTSService(
            api_key=os.getenv("DEEPGRAM_API_KEY"),
            voice=cfg.voice or "aura-helios-en",
        )

    def _create_cartesia_tts(self, user_language: str) -> Optional[Any]:
        cfg = self.tts_config
        speed_value = self.config.get("tts_speed", 1.0)
        speed_map = {0.85: "slow", 1.0: "normal", 1.15: "fast"}
        speed_value = speed_map[
            min(speed_map.keys(), key=lambda x: abs(x - speed_value))
        ]

        return self._create_cartesia_tts_service(
            model=cfg.model or "sonic-2",
            voice_id=cfg.voice or "95d51f79-c397-46f9-b49a-23763d3eaa2d",
            language=self.get_language(user_language),
            speed=speed_value,
        )

    def _create_google_tts(self, user_language: str) -> Optional[Any]:
        from pipecat.services.google.tts import GoogleTTSService

        cfg = self.tts_config
        return GoogleTTSService(
            credentials_path=os.getenv("GOOGLE_CREDENTIALS"),
            voice_id=cfg.voice,
            params=GoogleTTSService.InputParams(
                language=self.get_language(user_language),
                gender=self.config.get("gender", "female"),
            ),
        )

    def _create_lmnt_tts(self, user_language: str) -> Optional[Any]:
        from pipecat.services.lmnt.tts import LmntTTSService

        cfg = self.tts_config
        return LmntTTSService(
            api_key=os.getenv("LMNT_API_KEY"),
            voice_id=cfg.voice,
            model=cfg.model or "aurora",
            language=self.get_language(user_language),
            sample_rate=24000,
        )

    def _lookup_language_setting(
        self, config: Dict[str, Any], base_key: str, language_code: str
    ) -> Optional[Any]:
        """
        Resolve language-specific overrides for TTS configuration.
        """
        normalized = (language_code or "").lower()
        short = normalized.split("-")[0]
        candidates = [
            f"{base_key}_{normalized}",
            f"{base_key}_{short}",
        ]
        if normalized.startswith("en"):
            candidates.extend([f"{base_key}_english", f"{base_key}_en"])
        else:
            candidates.append(f"{base_key}_secondary")

        candidates.append(base_key)

        for key in candidates:
            if key in config and config[key]:
                return config[key]
        return None

    def _create_tts_service_for_language(self, language_code: str):
        """
        Create a TTS service instance configured for a specific language.
        """

        return self._create_tts_service()

    def _wrap_with_dual_tts(self, english_tts, secondary_tts):
        """
        Wrap TTS services with a dual-language router when secondary language exists.
        """
        if english_tts is None or secondary_tts is None:
            self._dual_language_tts = None
            self._current_tts_language = "en"
            return english_tts

        try:
            dual = DualLanguageTTS(
                english_tts=english_tts,
                secondary_tts=secondary_tts,
                secondary_language_code=self._secondary_language_code,
                logger=self._logger,
                on_language_change=self._handle_tts_language_change,
            )
        except Exception as exc:  # pragma: no cover - defensive guard
            self._logger.warning(
                "Dual-language TTS unavailable (%s); falling back to English-only", exc
            )
            self._dual_language_tts = None
            self._current_tts_language = "en"
            return english_tts

        self._dual_language_tts = dual
        self._current_tts_language = "en"
        dual.set_language("en")
        return dual

    def _prepare_tts_service(self):
        """
        Create TTS services with dual-language support when configured.
        """
        english_tts = self._create_tts_service_for_language("en")
        if not english_tts:
            self._logger.warning(
                "Failed to initialize English TTS service; falling back to default configuration"
            )
            english_tts = self._create_tts_service()

        self._english_tts_service = english_tts

        secondary_tts = None
        if (
            self._secondary_language_code
            and not self._secondary_language_code.startswith("en")
        ):
            secondary_tts = self._create_tts_service_for_language(
                self._secondary_language_code
            )
            if not secondary_tts:
                self._logger.warning(
                    "Secondary language TTS (%s) could not be created; continuing with English only",
                    self._secondary_language_code,
                )

        wrapped = self._wrap_with_dual_tts(english_tts, secondary_tts)
        if self._dual_language_tts:
            self._logger.info(
                "Dual-language TTS ready (English + %s)",
                self._secondary_language_code,
            )
        return wrapped

    def _handle_tts_language_change(self, language_code: Optional[str]) -> None:
        normalized = self._normalize_language_code(language_code) or "en"
        self._current_tts_language = normalized

    def _normalize_language_code(self, language_code: Optional[str]) -> Optional[str]:
        if not language_code:
            return None
        normalized = str(language_code).lower()
        if normalized.startswith("en"):
            return "en"
        if self._secondary_language_code and normalized.startswith(
            self._secondary_language_code
        ):
            return self._secondary_language_code
        if self._secondary_language_code and normalized.startswith(
            self._secondary_language_code.split("-")[0]
        ):
            return self._secondary_language_code
        return None

    def _guess_language(self, text: str) -> Optional[str]:
        if not text:
            return None
        if (
            self._secondary_language_code
            and not self._secondary_language_code.startswith("en")
        ):
            if any(ord(char) > 127 for char in text):
                return self._secondary_language_code
        return "en"

    def _update_tts_language(
        self, language_code: Optional[str], fallback_text: Optional[str] = None
    ) -> None:
        if not self._dual_language_tts:
            return
        normalized = self._normalize_language_code(language_code)
        if normalized is None:
            normalized = self._guess_language(fallback_text or "")
        if normalized is None:
            normalized = "en"
        if normalized != self._current_tts_language:
            self._dual_language_tts.set_language(normalized)
            self._current_tts_language = normalized

    def get_language(self, language: str) -> str:
        """
        Convert language code to pipecat Language enum.

        Supports:
        - hi: Hindi
        - pa: Punjabi
        - ta: Tamil
        - ur: Urdu
        - en: English (default)

        Args:
            language: Language code string

        Returns:
            Pipecat Language enum value
        """
        from pipecat.transcriptions.language import Language

        if language == "hi":
            return Language.HI
        elif language == "pa":
            return Language.PA
        elif language == "ta":
            return Language.TA
        elif language == "ur":
            return Language.UR
        else:
            return Language.EN


# Convenience functions for direct service creation
async def create_llm_service(
    config: Dict[str, Any],
    logger: Optional[logging.Logger] = None,
    room_name: Optional[str] = None,
    tool_calling: bool = False,
    get_docs_callback: Optional[callable] = None,
) -> Optional[Any]:
    """
    Create LLM service directly without instantiating factory.

    Includes retry logic and fallback provider for resilience.

    Args:
        config: Configuration dictionary
        logger: Optional logger instance
        room_name: Optional room name for caching
        tool_calling: Whether tool calling is enabled
        get_docs_callback: Optional callback for knowledge base retrieval

    Returns:
        Configured LLM service instance or None
    """
    factory = ServiceFactory(config, logger, room_name, tool_calling, get_docs_callback)
    return (
        await factory._create_llm_service_with_retry()
    )  # ✅ Uses retry wrapper (was _create_llm_service)


async def create_stt_service(
    config: Dict[str, Any], logger: Optional[logging.Logger] = None, context: str = ""
) -> Optional[Any]:
    """
    Create STT service directly without instantiating factory.

    Includes retry logic and fallback provider for resilience.

    Args:
        config: Configuration dictionary
        logger: Optional logger instance
        context: Optional context for improved transcription

    Returns:
        Configured STT service instance or None
    """
    factory = ServiceFactory(config, logger)
    return await factory._create_stt_service_with_retry(
        context
    )  # ✅ Uses retry wrapper (was _create_stt_service)


async def create_tts_service(
    config: Dict[str, Any], logger: Optional[logging.Logger] = None
) -> Optional[Any]:
    """
    Create TTS service directly without instantiating factory.

    Includes retry logic and fallback provider for resilience.

    Args:
        config: Configuration dictionary
        logger: Optional logger instance

    Returns:
        Configured TTS service instance or None
    """
    factory = ServiceFactory(config, logger)
    return (
        await factory._create_tts_service_with_retry()
    )  # ✅ Uses retry wrapper (was _create_tts_service)
