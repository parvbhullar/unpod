import os
import asyncio
import logging
import threading
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Lazy imports for livekit plugins - see initialization section below
# xai, google, openai, anthropic are imported conditionally to avoid import errors
from super.core.voice.common.common import add_perf_log
from super.core.voice.services.service_common import (
    DEFAULT_TTS_PROVIDER,
    DEFAULT_TTS_MODEL,
    DEFAULT_TTS_VOICE,
    UNPOD_TO_INWORLD_MODEL_MAP,
    normalize_tts_provider_model,
    INFERENCE_LLM_MODELS,
    INFERENCE_STT_MODELS,
    INFERENCE_TTS_MODELS,
    INFERENCE_TTS_DEFAULT_VOICES,
    INFERENCE_ELEVENLABS_VOICES,
    MODELS_WITHOUT_TEMPERATURE_SUPPORT,
    DEEPGRAM_TTS_VOICES,
    STT_FALLBACK_CHAIN,
    LLM_FALLBACK_CHAIN,
    TTS_FALLBACK_CHAIN,
    STTConfig,
    LLMConfig,
    TTSConfig,
    ServiceCommon,
    PROVIDER_API_KEYS,
    MODEL_CONTEXT_LIMITS,
    get_model_context_limit,
    estimate_tokens,
    OPENAI_REALTIME_VOICES,
    OPENAI_REALTIME_MODELS,
    GEMINI_REALTIME_VOICES,
    GEMINI_REALTIME_MODELS,
    GEMINI_LANGUAGE_MAP,
    is_realtime_model,
)
from super.core.voice.prompts.language_accent import LANGUAGE_ACCENT_PROMPT
from time import perf_counter

load_dotenv(override=True)

__all__ = [
    "LiveKitServiceFactory",
    "LiveKitServiceMode",
    "ServiceConfig",
    "DEFAULT_TTS_PROVIDER",
    "DEFAULT_TTS_MODEL",
    "DEFAULT_TTS_VOICE",
    "UNPOD_TO_INWORLD_MODEL_MAP",
    "normalize_tts_provider_model",
    "INFERENCE_LLM_MODELS",
    "INFERENCE_STT_MODELS",
    "INFERENCE_TTS_MODELS",
    "INFERENCE_TTS_DEFAULT_VOICES",
    "INFERENCE_ELEVENLABS_VOICES",
    "MODELS_WITHOUT_TEMPERATURE_SUPPORT",
    "DEEPGRAM_TTS_VOICES",
    "STT_FALLBACK_CHAIN",
    "LLM_FALLBACK_CHAIN",
    "TTS_FALLBACK_CHAIN",
    "BackgroundAudioPlayer",
    "AudioConfig",
    "BuiltinAudioClip",
    "MODEL_CONTEXT_LIMITS",
    "get_model_context_limit",
    "estimate_tokens",
    "OPENAI_REALTIME_VOICES",
    "OPENAI_REALTIME_MODELS",
    "GEMINI_REALTIME_VOICES",
    "GEMINI_REALTIME_MODELS",
    "GEMINI_LANGUAGE_MAP",
]

# =============================================================================
# LiveKit Availability Check
# =============================================================================

LIVEKIT_AVAILABLE = False
AgentSession = None
inference = None
silero = None
deepgram = None
openai = None
groq = None
cartesia = None
google = None
elevenlabs = None
xai = None
anthropic = None
azure = None
TurnDetection = None
MultilingualModel = None
BackgroundAudioPlayer = None
AudioConfig = None
BuiltinAudioClip = None

try:
    from livekit.agents.voice import AgentSession as _AgentSession
    from livekit.agents import inference as _inference

    AgentSession = _AgentSession
    inference = _inference
    LIVEKIT_AVAILABLE = True

    # Background audio support (optional)
    try:
        from livekit.agents.voice.background_audio import (
            BackgroundAudioPlayer as _BackgroundAudioPlayer,
            AudioConfig as _AudioConfig,
            BuiltinAudioClip as _BuiltinAudioClip,
        )

        BackgroundAudioPlayer = _BackgroundAudioPlayer
        AudioConfig = _AudioConfig
        BuiltinAudioClip = _BuiltinAudioClip
    except ImportError:
        pass

except ImportError as e:
    logging.getLogger("livekit.services").warning(
        f"LiveKit core plugins not available: {e}"
    )


def _ensure_livekit_plugins_loaded(logger: Optional[logging.Logger] = None) -> bool:
    """Load LiveKit plugins on the main thread to avoid plugin registration errors."""
    global silero, deepgram, openai, cartesia, groq, google, elevenlabs, xai, anthropic, azure
    global TurnDetection, MultilingualModel, BackgroundAudioPlayer, AudioConfig, BuiltinAudioClip

    if silero is not None:
        return True

    if threading.current_thread() is not threading.main_thread():
        if logger:
            logger.warning(
                "LiveKit plugins must be registered on the main thread; "
                "deferring plugin import."
            )
        return False

    try:
        from livekit.plugins import silero as _silero
        from livekit.plugins import deepgram as _deepgram
        from livekit.plugins import openai as _openai

        silero = _silero
        deepgram = _deepgram
        openai = _openai

        try:
            from livekit.plugins import cartesia as _cartesia

            cartesia = _cartesia
        except ImportError:
            pass

        try:
            from livekit.plugins import groq as _groq

            groq = _groq
        except ImportError:
            pass

        try:
            from livekit.plugins import google as _google

            google = _google
        except ImportError:
            pass

        try:
            from livekit.plugins import elevenlabs as _elevenlabs

            elevenlabs = _elevenlabs
        except ImportError:
            pass

        try:
            from livekit.plugins import xai as _xai

            xai = _xai
        except ImportError:
            pass

        try:
            from livekit.plugins import azure as _azure

            azure = _azure
        except ImportError:
            pass

        try:
            from livekit.plugins import anthropic as _anthropic

            anthropic = _anthropic
        except ImportError:
            pass

        try:
            from openai.types.beta.realtime.session import TurnDetection as _TurnDetection

            TurnDetection = _TurnDetection
        except ImportError:
            pass

        try:
            from livekit.plugins.turn_detector.multilingual import (
                MultilingualModel as _MultilingualModel,
            )

            MultilingualModel = _MultilingualModel
        except ImportError:
            pass

        return True
    except ImportError as e:
        if logger:
            logger.warning(f"LiveKit plugin import failed: {e}")
        return False


# Preload plugins on process start (main thread) to avoid registration errors.
# This is safe if plugins are unavailable (ImportError is handled).
if os.getenv("LIVEKIT_PLUGIN_PRELOAD", "true").lower() == "true":
    _ensure_livekit_plugins_loaded(logging.getLogger("livekit.services"))


# =============================================================================
# Service Mode Constants
# =============================================================================


class LiveKitServiceMode:
    """Service mode constants."""

    INFERENCE = "inference"
    REALTIME = "realtime"
    STANDARD = "standard"


# =============================================================================
# Typed Configuration Dataclasses
# =============================================================================

# Nova-2 only languages (not supported by nova-3)
NOVA_2_ONLY_LANGUAGES: list[str] = ["hi", "ta", "kn", "te", "ml"]


@dataclass
class ServiceMode:
    stt_provider: str = ""
    tts_provider: str = ""
    llm_provider: str = ""
    llm_type: str = "plugin"
    stt_type: str = "plugin"
    tts_type: str = "plugin"


@dataclass
class ServiceConfig:
    """Configuration for a service (STT/LLM/TTS). Deprecated: use typed configs."""

    provider: str
    model: str
    voice: Optional[str] = None
    language: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# LiveKit Service Factory
# =============================================================================


class LiveKitServiceFactory:
    """
    Factory for creating LiveKit voice services.

    Supports three modes:
    1. Inference Mode: Uses inference.LLM/STT/TTS classes (LiveKit Cloud)
    2. Realtime Mode: Native realtime models (OpenAI, Gemini)
    3. Standard Mode: Plugin-based STT/LLM/TTS service objects

    Priority for inference mode:
    1. AGENT_INFRA_MODE=inference env var → check if model is supported
    2. Model exists in inference registry → auto-select inference
    3. Config flag (*_inference) → use if True

    Example:
        factory = LiveKitServiceFactory(config)

        # Auto-selects mode based on priority
        session = factory.create_session()

        # Or override mode explicitly
        session = factory.create_session(mode="inference")
    """

    # Deepgram supported languages (Nova-2 model)
    # Reference: https://developers.deepgram.com/docs/models-languages-overview
    DEEPGRAM_SUPPORTED_LANGUAGES = [
        "bg", "ca",  # Bulgarian, Catalan
        "zh", "zh-CN", "zh-Hans", "zh-TW", "zh-Hant", "zh-HK",  # Chinese variants
        "cs", "da", "da-DK", "nl", "nl-BE",  # Czech, Danish, Dutch, Flemish
        "en", "en-US", "en-AU", "en-GB", "en-NZ", "en-IN",  # English variants
        "et", "fi", "fr", "fr-CA",  # Estonian, Finnish, French
        "de", "de-CH", "el",  # German, Greek
        "hi", "hu", "id", "it",  # Hindi, Hungarian, Indonesian, Italian
        "ja", "ko", "ko-KR",  # Japanese, Korean
        "lv", "lt", "ms",  # Latvian, Lithuanian, Malay
        "no", "pl",  # Norwegian, Polish
        "pt", "pt-BR", "pt-PT",  # Portuguese
        "ro", "ru", "sk",  # Romanian, Russian, Slovak
        "es", "es-419",  # Spanish
        "sv", "sv-SE",  # Swedish
        "th", "th-TH",  # Thai
        "tr", "uk", "vi",  # Turkish, Ukrainian, Vietnamese
        "multi",  # Multilingual mode
    ]

    # Cache for lazily loaded plugins
    _plugin_cache: Dict[str, Any] = {}

    def __init__(
            self,
            config: Dict[str, Any],
            logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the LiveKit service factory.

        Args:
            config: Configuration dictionary with provider settings
            logger: Optional logger instance
        """
        if not LIVEKIT_AVAILABLE:
            raise ImportError(
                "LiveKit agents SDK not available. "
                "Install with: pip install 'livekit-agents[silero]'"
            )

        self._raw_config = config  # Keep raw config for backward compat
        self.config = config  # Alias for backward compat
        self._logger = logger or logging.getLogger("livekit.services")

        # Determine mode using priority chain:
        # 1. Database flag (llm_realtime) - source of truth
        # 2. Model name detection (LLM_REALTIME_MODELS list)
        # 3. Config/env fallback for non-realtime modes
        if config.get("llm_realtime"):
            self.mode = LiveKitServiceMode.REALTIME
            self._logger.info("Realtime mode enabled via database flag (llm_realtime=True)")
        elif is_realtime_model(config.get("llm_model", "")):
            self.mode = LiveKitServiceMode.REALTIME
            self._logger.info(
                f"Realtime mode enabled via model detection: {config.get('llm_model')}"
            )
        else:
            self.mode = config.get(
                "mode", os.getenv("AGENT_INFRA_MODE", LiveKitServiceMode.STANDARD)
            )

        # Speaking plan settings
        self.speaking_plan = config.get("speaking_plan", {})

        # Parse configs ONCE - single normalization point
        self._common = ServiceCommon(
            config,
            logger=self._logger,
            room_name=config.get("room_name", "default_room"),
            session_id=config.get("session_id", "default"),
        )
        self.stt_config: STTConfig = self._common.stt_config
        self.llm_config: LLMConfig = self._common.llm_config
        self.tts_config: TTSConfig = self._common.tts_config

        # Log received config for STT/TTS debugging
        self._logger.info(
            f"[FACTORY_INIT] LiveKitServiceFactory initialized (mode={self.mode}) - "
            f"stt={self.stt_config.provider}/{self.stt_config.model}, "
            f"llm={self.llm_config.provider}/{self.llm_config.model}, "
            f"tts={self.tts_config.provider}/{self.tts_config.model}/{self.tts_config.voice}"
        )

        self.service_modes = ServiceMode()

    # =========================================================================
    # Unified Provider Validation
    # =========================================================================

    def _validate_provider(self, provider: str) -> tuple[bool, str]:
        """
        Unified validation for any provider's API key.

        Args:
            provider: Provider name (lowercase)

        Returns:
            Tuple of (is_valid, error_message)
        """
        provider_key = provider.lower()
        # Azure uses different keys depending on service (LLM vs Speech)
        if provider_key == "azure":
            if os.getenv("AZURE_IN_API_KEY") or os.getenv("AZURE_SPEECH_API_KEY"):
                return True, ""
            return False, "AZURE_IN_API_KEY or AZURE_SPEECH_API_KEY not set for azure"

        # Qwen uses Cerbras API key
        if provider_key == "qwen":
            if os.getenv("CEREBRAS_API_KEY"):
                return True, ""
            return False, "CEREBRAS_API_KEY not set for qwen"

        # OpenRouter uses OpenRouter API key
        if provider_key == "openrouter":
            if os.getenv("OPENROUTER_API_KEY"):
                return True, ""
            return False, "OPENROUTER_API_KEY not set for openrouter"

        env_var = PROVIDER_API_KEYS.get(provider_key)
        if env_var and not os.getenv(env_var):
            return False, f"{env_var} not set for {provider}"
        return True, ""

    def _has_api_key(self, provider: str) -> bool:
        """Check if API key exists for provider."""
        is_valid, _ = self._validate_provider(provider)
        return is_valid

    # =========================================================================
    # Inference Verification
    # =========================================================================

    def verify_inference_config(self) -> dict[str, bool]:
        """
        Verify and log inference mode configuration for all services.

        Returns:
            Dict with service-wise inference status:
            {"stt": True/False, "llm": True/False, "tts": True/False, "all": True/False}
        """
        stt_inference = self._should_use_inference("stt")
        llm_inference = self._should_use_inference("llm")
        tts_inference = self._should_use_inference("tts")

        self._logger.info(
            f"STT: {'inference' if stt_inference else 'plugin'} "
            f"({self.stt_config.provider}/{self.stt_config.model})"
        )
        self._logger.info(
            f"LLM: {'inference' if llm_inference else 'plugin'} "
            f"({self.llm_config.provider}/{self.llm_config.model})"
        )
        self._logger.info(
            f"TTS: {'inference' if tts_inference else 'plugin'} "
            f"({self.tts_config.provider}/{self.tts_config.model})"
        )

        all_inference = stt_inference and llm_inference and tts_inference

        return {
            "stt": stt_inference,
            "llm": llm_inference,
            "tts": tts_inference,
            "all": all_inference,
        }

    # =========================================================================
    # Voice-Optimized Parameter Methods
    # =========================================================================

    def _get_voice_optimized_max_tokens(self) -> int:
        """
        Get voice-optimized max_tokens with validation.

        Voice interactions need balance:
        - Too low (< 300): Responses cut off mid-sentence
        - Sweet spot (500-800): Complete 2-3 sentence explanations
        - Too high (> 1000): Agent monologues, user loses interest

        Returns:
            Validated max_tokens value
        """
        max_tokens = self.llm_config.max_tokens

        if max_tokens < 300:
            self._logger.warning(
                f"max_tokens={max_tokens} is low for voice (<300). "
                "Responses may be cut off mid-sentence. Consider 500-800."
            )
        elif max_tokens > 1000:
            self._logger.warning(
                f"max_tokens={max_tokens} is high for voice (>1000). "
                "Responses may feel too long. Consider 500-800."
            )

        return max_tokens

    def _get_voice_optimized_temperature(self) -> float:
        """
        Get voice-optimized temperature with validation.

        Voice interactions need focused responses:
        - 0.3: Very focused, minimal creativity (FAQ, customer service)
        - 0.4-0.5: Balanced, natural conversation (recommended)
        - 0.7+: Creative but verbose, prone to rambling

        Returns:
            Validated temperature value
        """
        temperature = self.llm_config.temperature

        if temperature > 0.6:
            self._logger.warning(
                f"temperature={temperature} is high for voice (>0.6). "
                "Agent may ramble. Consider 0.3-0.5 for concise responses."
            )

        return temperature

    def _build_cache_key(self) -> str:
        """
        Build robust cache key with session and user context.

        Format: room:session:user_hash
        Prevents data leaks between users and stale cache across sessions.

        Returns:
            Cache key string
        """
        room_name = self.config.get("room_name", "default_room")
        session_id = self.config.get("session_id", "default")

        cache_key = f"{room_name}:{session_id}"
        self._logger.debug(f"LLM cache key generated: {cache_key}")
        return cache_key

    # =========================================================================
    # Inference Support Detection
    # =========================================================================

    def _model_supports_inference(self, service_type: str) -> bool:
        """
        Check if the configured model is supported by LiveKit Inference.

        Returns True only if provider AND model are in the inference registry.
        If not in registry, plugin mode will be used with same provider/model.

        Args:
            service_type: One of 'stt', 'llm', 'tts'

        Returns:
            True if the model is in the inference registry
        """
        if service_type == "stt":
            provider = self.stt_config.provider
            model = self.stt_config.model
            registry = INFERENCE_STT_MODELS
        elif service_type == "llm":
            provider = self.llm_config.provider
            model = self.llm_config.model
            registry = INFERENCE_LLM_MODELS
        elif service_type == "tts":
            provider = self.tts_config.provider
            model = self.tts_config.model
            registry = INFERENCE_TTS_MODELS
        else:
            return False

        if provider not in registry:
            return False

        return model in registry[provider]

    def _is_voice_inference_compatible(self, provider: str, voice: str) -> bool:
        """
        Check if the voice is compatible with LiveKit inference mode.

        Some providers (like ElevenLabs) only support certain pre-made voices
        in inference mode. Custom/cloned voices must use plugin mode.

        Args:
            provider: TTS provider name (lowercase)
            voice: Voice ID or name

        Returns:
            True if the voice is inference-compatible
        """
        if provider == "elevenlabs":
            # ElevenLabs inference only supports pre-made voices
            # Custom/cloned voices must use plugin mode
            if voice in INFERENCE_ELEVENLABS_VOICES:
                return True
            self._logger.debug(
                f"ElevenLabs voice '{voice}' not in inference-compatible list. "
                "Will use plugin mode for custom/cloned voices."
            )
            return False
        elif provider == "cartesia":
            # Cartesia uses UUIDs - all are inference-compatible
            return True
        elif provider == "deepgram":
            # Deepgram requires specific voice names
            return voice.lower() in DEEPGRAM_TTS_VOICES
        elif provider == "rime":
            # Rime voices are inference-compatible
            return True
        elif provider == "inworld":
            # Inworld voices are inference-compatible
            return True

        # Unknown provider - assume compatible
        return True

    def _should_use_inference(self, service_type: str) -> bool:
        """
        Determine if inference mode should be used for a service type.

        Priority:
        1. Provider must be in inference registry — providers with their own
           auth/endpoints (Azure, Cerebras, Ollama, AWS, etc.) always use plugin
        2. AGENT_INFRA_MODE env var (if 'inference', check model support)
        3. Config flag fallback (*_inference) — only for registry providers

        For TTS, also validates that the voice is inference-compatible.
        Custom/cloned voices (e.g., ElevenLabs) may not be available in inference mode.

        Args:
            service_type: One of 'stt', 'llm', 'tts'

        Returns:
            True if inference mode should be used
        """
        env_mode = os.getenv("AGENT_INFRA_MODE", "").lower()
        if env_mode != "inference":
            return False

        model_supported = self._model_supports_inference(service_type)
        config_flag = self._get_inference_flag(f"{service_type}_inference")

        # Provider not in inference registry → always use plugin.
        # Providers like Azure, Cerebras, Ollama, AWS need their own
        # auth/endpoints that LiveKit Cloud inference doesn't support.
        # The config flag should only promote to inference for providers
        # that are actually in the registry.
        if not model_supported and not config_flag:
            return False

        if not model_supported and config_flag:
            # Config flag is set, but provider isn't in registry.
            # Log and fall back to plugin — inference would fail.
            if service_type == "llm":
                provider = self.llm_config.provider
            elif service_type == "stt":
                provider = self.stt_config.provider
            else:
                provider = self.tts_config.provider

            # For TTS, allow the flag to work (TTS inference supports
            # broader providers via voice_inference flag).
            if service_type == "tts":
                self._logger.info(
                    f"TTS inference flag is True in database. "
                    f"Using {self.tts_config.model} despite not being in registry."
                )
            else:
                self._logger.info(
                    f"{service_type.upper()} provider '{provider}' not in inference "
                    f"registry. Using plugin mode despite {service_type}_inference flag."
                )
                return False

        inference_mode = True

        # For TTS, also check voice compatibility
        if service_type == "tts":
            cfg = self.tts_config
            if not self._is_voice_inference_compatible(cfg.provider, cfg.voice):
                if self.config.get("voice_inference", False):
                    self._logger.info(
                        f"  TTS voice '{cfg.voice}' is instance compatible {cfg.provider}."
                    )
                    return True

                self._logger.info(
                    f"TTS voice '{cfg.voice}' not inference-compatible for {cfg.provider}. "
                    "Using plugin mode instead."
                )
                return False
        return inference_mode

    # =========================================================================
    # Unified Service Creation (Entry Points)
    # =========================================================================

    def create_stt(self) -> Any:
        """
        Create STT service - returns inference.STT or plugin STT.

        Uses priority logic to decide between inference and plugin mode.

        Returns:
            inference.STT instance or plugin STT instance
        """
        cfg = self.stt_config
        use_inference = self._should_use_inference("stt")

        self._logger.info(
            f"STT: {'inference' if use_inference else 'plugin'} "
            f"({cfg.provider}/{cfg.model})"
        )

        if use_inference:
            return self._create_inference_stt()

        return self._create_plugin_stt()

    def create_llm(self) -> Any:
        """
        Create LLM service - returns inference.LLM or plugin LLM.

        Uses priority logic to decide between inference and plugin mode.

        Returns:
            inference.LLM instance or plugin LLM instance
        """
        cfg = self.llm_config
        use_inference = self._should_use_inference("llm")

        self._logger.info(
            f"LLM: {'inference' if use_inference else 'plugin'} "
            f"({cfg.provider}/{cfg.model})"
        )

        if use_inference:
            return self._create_inference_llm()
        return self._create_plugin_llm()

    def create_tts(self) -> Any:
        """
        Create TTS service - returns inference.TTS or plugin TTS.

        Priority:
        1. If model is in inference registry → use inference mode
        2. If model NOT in registry → use plugin mode with same provider/model
        3. Fallback to default happens in create_tts_with_retry() if plugin fails

        Returns:
            inference.TTS instance or plugin TTS instance
        """
        cfg = self.tts_config  # Already normalized in __post_init__
        use_inference = self._should_use_inference("tts")

        self._logger.info(
            f"TTS: {'inference' if use_inference else 'plugin'} "
            f"({cfg.provider}/{cfg.model})"
        )

        if use_inference:
            return self._create_inference_tts()
        return self._create_plugin_tts()

    # =========================================================================
    # Service Creation with Retry Logic
    # =========================================================================

    async def create_stt_with_retry(self) -> Any:
        """
        Create STT service with exponential backoff retry and fallback chain.

        Retry strategy:
        - Attempts: Configurable via STT_RETRY_ATTEMPTS env or config
        - Backoff: Fast exponential (0.5s, 1s) for startup optimization
        - Fallback chain: Tries alternative providers if primary fails

        Returns:
            STT service instance or fallback on failure
        """
        max_retries = int(
            os.getenv("STT_RETRY_ATTEMPTS", self.config.get("stt_retry_attempts", 2))
        )
        backoff_multiplier = float(
            os.getenv("STT_RETRY_BACKOFF", self.config.get("stt_retry_backoff", 0.5))
        )

        # Try primary provider first
        for attempt in range(1, max_retries + 1):
            try:
                service = self.create_stt()

                try:
                    if self.service_modes.stt_type != "inference":
                        self.service_modes.stt_provider = service.provider
                except Exception as e:
                    pass

                if service:
                    if attempt > 1:
                        self._logger.info(
                            f"STT service created on attempt {attempt}/{max_retries}"
                        )
                    return service
            except Exception as e:
                self._logger.error(
                    f"STT creation failed (attempt {attempt}/{max_retries}): {e}"
                )
                if attempt < max_retries:
                    wait_time = backoff_multiplier ** attempt
                    await asyncio.sleep(wait_time)

        # Primary failed, try fallback chain
        self._logger.warning("Primary STT failed, trying fallback chain")
        return await self._create_stt_from_fallback_chain()

    async def _create_stt_from_fallback_chain(self) -> Any:
        """Try each provider in the STT fallback chain until one succeeds."""
        current_provider = self.config.get("stt_provider", "").lower()
        current_model = self.config.get("stt_model", "")

        for fallback in STT_FALLBACK_CHAIN:
            provider = fallback["provider"]
            model = fallback["model"]

            # Skip if this is the same as the primary that just failed
            if provider == current_provider and model == current_model:
                continue

            try:
                self._logger.info(f"Trying STT fallback: {provider}/{model}")
                stt = self._create_stt_for_provider(provider, model)
                if stt:
                    self._logger.info(f"STT fallback succeeded: {provider}/{model}")
                    return stt
            except Exception as e:
                self._logger.warning(f"STT fallback {provider}/{model} failed: {e}")
                continue

        # Ultimate fallback: Deepgram with defaults
        self._logger.warning("All STT fallbacks failed, using Deepgram defaults")
        return deepgram.STT()

    def _create_stt_for_provider(self, provider: str, model: str) -> Any:
        """Create STT service for a specific provider/model combination."""
        language = self.config.get("language", "en")

        if provider == "deepgram":
            return deepgram.STT(
                model=model,
                language=language,
                punctuate=True,
                smart_format=True,
            )
        elif provider == "openai":
            return openai.STT(model=model, language=language)
        elif provider == "google" and google:
            return google.STT(
                model=model,
                credentials_file=os.getenv("GOOGLE_CREDENTIALS"),
            )
        else:
            return deepgram.STT()

    async def create_llm_with_retry(self) -> Any:
        """
        Create LLM service with exponential backoff retry and fallback chain.

        Retry strategy:
        - Attempts: Configurable via LLM_RETRY_ATTEMPTS env or config
        - Backoff: Fast exponential with extended wait for rate limits
        - Fallback chain: Tries alternative providers if primary fails

        Returns:
            LLM service instance or fallback on failure
        """
        max_retries = int(
            os.getenv("LLM_RETRY_ATTEMPTS", self.config.get("llm_retry_attempts", 2))
        )
        backoff_multiplier = float(
            os.getenv("LLM_RETRY_BACKOFF", self.config.get("llm_retry_backoff", 0.5))
        )

        for attempt in range(1, max_retries + 1):
            try:
                service = self.create_llm()

                try:
                    if self.service_modes.llm_type != "inference":
                        self.service_modes.llm_provider = service.provider
                except Exception as e:
                    pass
                if service:
                    if attempt > 1:
                        self._logger.info(
                            f"LLM service created on attempt {attempt}/{max_retries}"
                        )
                    return service
            except Exception as e:
                error_msg = str(e)
                self._logger.error(
                    f"LLM creation failed (attempt {attempt}/{max_retries}): {error_msg}"
                )

                # Extended backoff for rate limits
                if "rate" in error_msg.lower() or "429" in error_msg:
                    wait_time = (backoff_multiplier ** attempt) * 2
                    self._logger.warning(f"Rate limit detected, waiting {wait_time}s")
                else:
                    wait_time = backoff_multiplier ** attempt

                if attempt < max_retries:
                    await asyncio.sleep(wait_time)

        # Primary failed, try fallback chain
        self._logger.warning("Primary LLM failed, trying fallback chain")
        return await self._create_llm_from_fallback_chain()

    async def _create_llm_from_fallback_chain(self) -> Any:
        """Try each provider in the LLM fallback chain until one succeeds."""
        current_provider = self.config.get("llm_provider", "").lower()
        current_model = self.config.get("llm_model", "")
        temperature = self._get_voice_optimized_temperature()

        for fallback in LLM_FALLBACK_CHAIN:
            provider = fallback["provider"]
            model = fallback["model"]

            # Skip if this is the same as the primary that just failed
            if provider == current_provider and model == current_model:
                continue

            try:
                self._logger.info(f"Trying LLM fallback: {provider}/{model}")
                llm = self._create_llm_for_provider(provider, model, temperature)
                if llm:
                    self._logger.info(f"LLM fallback succeeded: {provider}/{model}")
                    return llm
            except Exception as e:
                self._logger.warning(f"LLM fallback {provider}/{model} failed: {e}")
                continue

        # Ultimate fallback: OpenAI gpt-4o-mini
        self._logger.warning("All LLM fallbacks failed, using OpenAI gpt-4o-mini")
        return openai.LLM(model="gpt-4o-mini", temperature=0.4)

    def _create_llm_for_provider(
            self, provider: str, model: str, temperature: float
    ) -> Any:
        """Create LLM service for a specific provider/model combination."""
        if provider == "openai":
            return openai.LLM(
                model=model,
                temperature=temperature,
                parallel_tool_calls=True,
            )
        elif provider == "groq" and groq:
            return groq.LLM(
                model=model,
                temperature=temperature,
                parallel_tool_calls=True,
            )
        elif provider in ("google", "gemini") and google:
            return google.LLM(model=model, temperature=temperature)
        else:
            return openai.LLM(model="gpt-4o-mini", temperature=0.4)

    async def create_tts_with_retry(self) -> Any:
        """
        Create TTS service with exponential backoff retry and fallback chain.

        Retry strategy:
        - Attempts: Configurable via TTS_RETRY_ATTEMPTS env or config
        - Backoff: Fast exponential (0.5s, 1s) for startup optimization
        - Fallback chain: Tries alternative providers if primary fails

        Returns:
            TTS service instance or fallback on failure
        """
        max_retries = int(
            os.getenv("TTS_RETRY_ATTEMPTS", self.config.get("tts_retry_attempts", 2))
        )
        backoff_multiplier = float(
            os.getenv("TTS_RETRY_BACKOFF", self.config.get("tts_retry_backoff", 0.5))
        )

        for attempt in range(1, max_retries + 1):
            try:
                service = self.create_tts()
                try:
                    if self.service_modes.tts_type != "inference":
                        self.service_modes.tts_provider = service.provider
                except Exception as e:
                    pass

                if service:
                    if attempt > 1:
                        self._logger.info(
                            f"TTS service created on attempt {attempt}/{max_retries}"
                        )
                    return service
            except Exception as e:
                self._logger.error(
                    f"TTS creation failed (attempt {attempt}/{max_retries}): {e}"
                )
                if attempt < max_retries:
                    wait_time = backoff_multiplier ** attempt
                    await asyncio.sleep(wait_time)

        # Primary failed, try fallback chain
        self._logger.warning("Primary TTS failed, trying fallback chain")
        return await self._create_tts_from_fallback_chain()

    async def _create_tts_from_fallback_chain(self) -> Any:
        """Try each provider in the TTS fallback chain until one succeeds."""
        current_provider = self.tts_config.provider
        current_model = self.tts_config.model

        for fallback in TTS_FALLBACK_CHAIN:
            provider = fallback["provider"]
            model = fallback["model"]
            voice = fallback.get("voice", "")

            # Skip if this is the same as the primary that just failed
            if provider == current_provider and model == current_model:
                continue

            try:
                self._logger.info(f"Trying TTS fallback: {provider}/{model}")
                tts = self._create_tts_for_provider(provider, model, voice)
                if tts:
                    self._logger.info(f"TTS fallback succeeded: {provider}/{model}")
                    return tts
            except Exception as e:
                self._logger.warning(f"TTS fallback {provider}/{model} failed: {e}")
                continue

        # Ultimate fallback: Cartesia or OpenAI
        self._logger.warning("All TTS fallbacks failed, using ultimate fallback")
        return self._create_fallback_tts()

    def _create_tts_for_provider(self, provider: str, model: str, voice: str) -> Any:
        """
        Create TTS service for a specific provider/model combination.

        Delegates to _create_plugin_tts() with temporary config override.
        This ensures consistent TTS creation with all validations and parameters.
        """
        # Store original config values
        original_provider = self.config.get("tts_provider")
        original_model = self.config.get("tts_model")
        original_voice = self.config.get("tts_voice")

        try:
            # Temporarily override config
            self.config["tts_provider"] = provider
            self.config["tts_model"] = model
            self.config["tts_voice"] = voice

            # Delegate to the main plugin TTS creation
            return self._create_plugin_tts()
        finally:
            # Restore original config
            self.config["tts_provider"] = original_provider
            self.config["tts_model"] = original_model
            self.config["tts_voice"] = original_voice

    # =========================================================================
    # Inference Service Creators (using inference.* classes)
    # =========================================================================

    def _create_inference_stt(self) -> Any:
        """
        Create STT using inference module with extra_kwargs support.

        Handles provider-specific extra parameters:
        - Cartesia: min_volume, max_silence_duration_secs
        - AssemblyAI: format_turns, end_of_turn_confidence_threshold, etc.
        - Deepgram: generic API params

        Returns:
            inference.STT instance
        """
        cfg = self.stt_config
        language = cfg.language

        self.service_modes.stt_type = "inference"

        # Language is controlled by database config for all models
        # No hardcoded overrides - respect the database setting

        # Build provider-specific extra_kwargs
        extra_kwargs = self._build_inference_stt_extra_kwargs(cfg.provider, cfg)

        # Model already normalized in STTConfig.__post_init__ for nova-3 restrictions
        model_ref = f"{cfg.provider}/{cfg.model}"
        self._logger.info(
            f"Creating inference STT: {model_ref}:{language} "
            f"(extra_kwargs={extra_kwargs})"
        )

        self.service_modes.stt_provider = model_ref

        return inference.STT(
            model=model_ref,
            language=language,
            extra_kwargs=extra_kwargs ,
        )

    def _build_inference_stt_extra_kwargs(
            self, provider: str, cfg: STTConfig
    ) -> Dict[str, Any]:
        """
        Build provider-specific extra_kwargs for inference STT.

        Based on LiveKit Inference STT documentation:
        - Cartesia: min_volume, max_silence_duration_secs
        - AssemblyAI: format_turns, end_of_turn_confidence_threshold,
                      min_end_of_turn_silence_when_confident, max_turn_silence,
                      keyterms_prompt
        - Deepgram: generic API params

        Args:
            provider: STT provider name (normalized)
            cfg: STTConfig with provider-specific settings

        Returns:
            Dict of extra_kwargs to pass to inference.STT()
        """
        extra_kwargs: Dict[str, Any] = {}

        if provider == "cartesia":
            # Cartesia: min_volume, max_silence_duration_secs
            if cfg.min_volume is not None:
                extra_kwargs["min_volume"] = cfg.min_volume
            if cfg.max_silence_duration_secs is not None:
                extra_kwargs["max_silence_duration_secs"] = cfg.max_silence_duration_secs

        elif provider == "assemblyai":
            # AssemblyAI: turn detection params
            if cfg.format_turns is not None:
                extra_kwargs["format_turns"] = cfg.format_turns
            if cfg.end_of_turn_confidence_threshold is not None:
                extra_kwargs["end_of_turn_confidence_threshold"] = (
                    cfg.end_of_turn_confidence_threshold
                )
            if cfg.min_end_of_turn_silence_when_confident is not None:
                extra_kwargs["min_end_of_turn_silence_when_confident"] = (
                    cfg.min_end_of_turn_silence_when_confident
                )
            if cfg.max_turn_silence is not None:
                extra_kwargs["max_turn_silence"] = cfg.max_turn_silence
            if cfg.keyterms_prompt:
                extra_kwargs["keyterms_prompt"] = cfg.keyterms_prompt

        elif provider == "deepgram":
            # Deepgram: pass through plugin params as extra_kwargs for faster EOU
            # Note: inference API may support different params than plugin
            extra_kwargs["interim_results"] = cfg.extra.get("interim_results", True)
            extra_kwargs["endpointing_ms"] = cfg.endpointing_ms  # Default 20ms for faster endpointing
            extra_kwargs["no_delay"] = cfg.extra.get("no_delay", True)
            # Max silence before ending utterance (faster EOU detection)
            utterance_end_ms = cfg.extra.get("utterance_end_ms")
            if utterance_end_ms is not None:
                extra_kwargs["utterance_end_ms"] = utterance_end_ms
            if cfg.smart_format:
                extra_kwargs["smart_format"] = cfg.smart_format
            if cfg.filler_words:
                extra_kwargs["filler_words"] = cfg.filler_words
            if cfg.profanity_filter:
                extra_kwargs["profanity_filter"] = cfg.profanity_filter

        return extra_kwargs

    def _model_supports_temperature(self, provider: str, model: str) -> bool:
        """
        Check if the model supports custom temperature values.

        Some models (like gpt-5-mini) only support the default temperature (1)
        and return errors when custom values are passed.

        Args:
            provider: LLM provider name (e.g., 'openai', 'google')
            model: Model name (e.g., 'gpt-5-mini')

        Returns:
            True if the model supports custom temperature, False otherwise
        """
        unsupported_models = MODELS_WITHOUT_TEMPERATURE_SUPPORT.get(provider, [])
        return model not in unsupported_models

    def _create_inference_llm(self) -> Any:
        """
        Create LLM using inference module with extra_kwargs support.

        Supports:
        - max_completion_tokens (voice-optimized with validation)
        - temperature (voice-optimized with validation, if model supports it)
        - reasoning_effort (for o1/o3 models)
        - parallel_tool_calls (for function calling)

        Returns:
            inference.LLM instance
        """
        cfg = self.llm_config  # Already normalized in __post_init__

        self.service_modes.llm_type = "inference"
        # Get voice-optimized parameters with validation
        max_tokens = self._get_voice_optimized_max_tokens()
        temperature = self._get_voice_optimized_temperature()

        # Build extra_kwargs from config
        extra_kwargs: Dict[str, Any] = {}

        if max_tokens:
            extra_kwargs["max_completion_tokens"] = max_tokens

        # Only add temperature if the model supports it
        if temperature is not None and self._model_supports_temperature(
                cfg.provider, cfg.model
        ):
            extra_kwargs["temperature"] = temperature
        elif temperature is not None:
            self._logger.info(
                f"Model '{cfg.model}' does not support custom temperature, using default"
            )

        # Reasoning effort for o1/o3 models only (OpenAI reasoning models)
        if cfg.reasoning_effort and cfg.provider == "openai" and (
                "o1" in cfg.model.lower() or "o3" in cfg.model.lower()
        ):
            extra_kwargs["reasoning_effort"] = cfg.reasoning_effort

        # Parallel tool calls (pass through to Chat Completions API)
        if cfg.parallel_tool_calls is not None:
            extra_kwargs["parallel_tool_calls"] = cfg.parallel_tool_calls

        model_ref = f"{cfg.provider}/{cfg.model}"
        self._logger.info(
            f"Creating inference LLM: {model_ref} (extra_kwargs={extra_kwargs})"
        )

        self.service_modes.llm_provider = model_ref
        return inference.LLM(
            model=model_ref,
            extra_kwargs=extra_kwargs if extra_kwargs else None,
        )

    def _create_inference_tts(self) -> Any:
        """
        Create TTS using inference module with extra_kwargs support.

        Handles provider-specific voice validation and extra parameters:
        - Cartesia: speed, volume, emotion
        - Deepgram: generic API params
        - ElevenLabs: inactivity_timeout, apply_text_normalization
        - Inworld: generic API params
        - Rime: generic API params

        Falls back to default TTS if:
        - Model is not valid in the inference registry

        Returns:
            inference.TTS instance
        """
        cfg = self.tts_config  # Already normalized in __post_init__
        provider = cfg.provider
        model = cfg.model
        voice = cfg.voice
        language = cfg.language

        self.service_modes.tts_type = "inference"
        # Handle invalid models - fallback to default TTS
        if self._should_fallback_tts(provider, model):
            fallback_provider = DEFAULT_TTS_PROVIDER
            fallback_model = os.getenv("FALLBACK_TTS_MODEL", DEFAULT_TTS_MODEL)
            fallback_voice = os.getenv("FALLBACK_TTS_VOICE", DEFAULT_TTS_VOICE)
            self._logger.warning(
                f"TTS provider '{provider}' with model '{model}' is not valid. "
                f"Falling back to {fallback_provider} {fallback_model}"
            )
            provider = fallback_provider
            model = fallback_model
            voice = fallback_voice
        else:
            # Validate and normalize voice for each provider
            voice = self._validate_tts_voice(provider, voice)

        # Build provider-specific extra_kwargs
        extra_kwargs = self._build_inference_tts_extra_kwargs(provider, cfg)

        model_ref = f"{provider}/{model}"
        self._logger.info(
            f"Creating inference TTS: {model_ref}:{voice} "
            f"(extra_kwargs={extra_kwargs})"
        )

        self.service_modes.tts_provider = model_ref

        # Build TTS kwargs - only include extra_kwargs if non-empty
        # Note: passing None for extra_kwargs causes "'NoneType' object is not iterable"
        tts_kwargs: Dict[str, Any] = {
            "model": model_ref,
            "voice": voice,
            "language": language,
        }
        if extra_kwargs:
            tts_kwargs["extra_kwargs"] = extra_kwargs

        return inference.TTS(**tts_kwargs)

    def _build_inference_tts_extra_kwargs(
            self, provider: str, cfg: TTSConfig
    ) -> Dict[str, Any]:
        """
        Build provider-specific extra_kwargs for inference TTS.

        Based on LiveKit Inference TTS documentation:
        - Cartesia: speed, volume, emotion
        - Deepgram: generic API params
        - ElevenLabs: inactivity_timeout, apply_text_normalization
        - Inworld: generic API params
        - Rime: generic API params

        Args:
            provider: TTS provider name (normalized)
            cfg: TTSConfig with provider-specific settings

        Returns:
            Dict of extra_kwargs to pass to inference.TTS()
        """
        extra_kwargs: Dict[str, Any] = {}

        if provider == "cartesia":
            # Cartesia: speed (0.6-2.0), volume (multiplier), emotion
            if cfg.speed != 1.0:
                extra_kwargs["speed"] = cfg.speed
            if cfg.volume != 1.0:
                extra_kwargs["volume"] = cfg.volume
            if cfg.emotion:
                extra_kwargs["emotion"] = cfg.emotion

        elif provider == "elevenlabs":
            # ElevenLabs: inactivity_timeout, apply_text_normalization
            if cfg.extra.get("inactivity_timeout"):
                extra_kwargs["inactivity_timeout"] = cfg.extra["inactivity_timeout"]
            if cfg.extra.get("apply_text_normalization") is not None:
                extra_kwargs["apply_text_normalization"] = cfg.extra[
                    "apply_text_normalization"
                ]
            # Also support voice_settings style params if needed
            if cfg.stability is not None:
                extra_kwargs["stability"] = cfg.stability
            if cfg.similarity_boost is not None:
                extra_kwargs["similarity_boost"] = cfg.similarity_boost

        elif provider == "deepgram":
            # Deepgram: pass through any extra params from config
            # The API supports additional params via extra_kwargs
            pass  # No specific params documented, but allow passthrough

        elif provider == "inworld":
            # Inworld: generic API params
            if cfg.speed != 1.0:
                # Ensure speaking_rate is always valid (> 0)
                speaking_rate = max(cfg.speed, 0.1) if cfg.speed > 0 else 1.0
                extra_kwargs["speaking_rate"] = speaking_rate
            if cfg.temperature is not None:
                extra_kwargs["temperature"] = cfg.temperature

        elif provider == "rime":
            # Rime: generic API params (not specifically documented)
            if cfg.speed != 1.0:
                extra_kwargs["speed"] = cfg.speed

        return extra_kwargs

    def _get_inference_flag(self, config_key: str) -> bool:
        """
        Get inference flag from config, handling DBeaver checkbox format.

        DBeaver shows [v] for true and [] for false in boolean fields.
        These are stored as strings and need special handling.

        Args:
            config_key: Configuration key (e.g., "tts_inference", "stt_inference")

        Returns:
            True if inference flag is set, False otherwise
        """
        inference_value = self.config.get(config_key, False)

        # Handle DBeaver checkbox format: [v] = true, [] = false
        if isinstance(inference_value, str):
            return inference_value.strip() == "[v]"
        else:
            return bool(inference_value)

    def _should_fallback_tts(self, provider: str, model: str) -> bool:
        """
        Check if TTS should fallback to default provider.

        Returns True if:
        - Provider is not in inference registry
        - Model is not valid for the provider
        - AND database inference flag is not True

        Args:
            provider: TTS provider name
            model: TTS model name

        Returns:
            True if fallback is needed
        """
        # Handle 'unpod' as special alias
        if provider == "unpod":
            return True

        # Check if database inference flag is set - if True, don't fallback
        if self._get_inference_flag("tts_inference"):
            self._logger.info(
                f"TTS inference flag is True in database. "
                f"Using {provider}/{model} despite not being in registry."
            )
            return False

        # Check if provider exists in registry
        if provider not in INFERENCE_TTS_MODELS:
            return True

        # Check if model is valid for provider
        valid_models = INFERENCE_TTS_MODELS.get(provider, [])
        return model not in valid_models

    def _validate_tts_voice(self, provider: str, voice: str) -> str:
        """Validate and normalize TTS voice for the given provider."""
        return self._common.validate_tts_voice(provider, voice)

    def _looks_like_uuid(self, value: str) -> bool:
        """Check if a string looks like a UUID."""
        return self._common.looks_like_uuid(value)

    # =========================================================================
    # Plugin Service Creators (using livekit.plugins.*)
    # =========================================================================

    def _create_plugin_stt(self) -> Any:
        """Create STT service using plugins."""
        if not _ensure_livekit_plugins_loaded(self._logger):
            raise RuntimeError(
                "LiveKit plugins must be initialized on the main thread."
            )
        cfg = self.stt_config
        provider = cfg.provider
        model = cfg.model
        language = cfg.language
        self.service_modes.stt_type = "plugin"

        # Deepgram: default to "multi" for unsupported languages
        if provider == "deepgram":
            if not language or language not in self.DEEPGRAM_SUPPORTED_LANGUAGES:
                language = "multi"

        # Validate provider API key - fallback to Deepgram if missing
        is_valid, error_msg = self._validate_provider(provider)
        if not is_valid and provider != "deepgram":
            self._logger.warning(f"{error_msg}. Falling back to Deepgram.")
            # Check if Deepgram API key is available
            deepgram_valid, _ = self._validate_provider("deepgram")
            if deepgram_valid:
                return deepgram.STT(
                    model="nova-3",
                    language=language,
                    punctuate=True,
                    smart_format=True,
                )
            else:
                # Last resort: try OpenAI
                self._logger.warning("Deepgram API key also missing, trying OpenAI")
                return openai.STT(model="whisper-1", language=language)

        try:
            if provider == "openai":
                return openai.STT(model=model, language=language)

            elif provider == "deepgram":
                # Configure Deepgram STT with improved transcription options
                # See: https://docs.livekit.io/agents/models/stt/plugins/deepgram/

                if cfg.use_finals_only:
                    self._logger.info(
                        "Deepgram STT: Using final transcriptions only (interim_results=False)"
                    )

                return deepgram.STT(
                    model=model,
                    language=language,
                    punctuate=True,  # Add punctuation for better turn detection
                    smart_format=cfg.smart_format,
                    filler_words=cfg.filler_words,
                    endpointing_ms=cfg.endpointing_ms,
                    interim_results=not cfg.use_finals_only,
                    profanity_filter=cfg.profanity_filter,
                )

            elif provider == "cartesia":
                from livekit.plugins import cartesia

                return cartesia.STT(model=model, language=language)

            elif provider == "groq" and groq:
                return groq.STT(model=model)

            elif provider == "fal":
                from livekit.plugins import fal

                return fal.STT(language=language)

            elif provider == "gladia":
                from livekit.plugins import gladia

                svc = self._lazy_import_plugin("gladia")

                if svc:
                    return svc.STT(
                        api_key=os.getenv("GLADIA_API_KEY"),
                    )

                return gladia.STT(
                    api_key=os.getenv("GLADIA_API_KEY"),
                )

            elif provider == "soniox":
                from livekit.plugins import soniox

                stt_opts = soniox.STTOptions(model=model)
                if language:
                    stt_opts.language_hints = [language]
                if cfg.keyterms_prompt:
                    stt_opts.context = cfg.keyterms_prompt

                return soniox.STT(
                    api_key=os.getenv("SONIOX_API_KEY"),
                    params=stt_opts,
                )

            elif provider == "speechmatics":
                svc = self._lazy_import_plugin("speechmatics")
                if svc:
                    return svc.STT()

            elif provider == "sarvam":
                svc = self._lazy_import_plugin("sarvam")
                if svc:
                    return svc.STT(language="hi-IN", model=model)

            elif provider == "google" and google:
                return google.STT(
                    spoken_punctuation=False,
                    model=model,
                    credentials_file=os.getenv("GOOGLE_CREDENTIALS"),
                )

            elif provider == "aws":
                svc = self._lazy_import_plugin("aws")
                if svc:
                    aws_region = self.config.get(
                        "aws_region", os.getenv("AWS_REGION", "ap-south-1")
                    )
                    return svc.STT(language=language, region=aws_region)

            elif provider == "azure":
                from livekit.plugins import azure

                return azure.STT(
                    speech_key=os.getenv("AZURE_SPEECH_API_KEY"),
                    speech_region=os.getenv("AZURE_SPEECH_REGION"),
                )

            elif provider == "assemblyai":
                from livekit.plugins import assemblyai

                return assemblyai.STT(
                    api_key=os.getenv("ASSEMBLYAI_API_KEY"),
                    model=model,
                )

            elif provider == "gladia":
                from livekit.plugins import gladia

                svc = self._lazy_import_plugin("gladia")
                if svc:
                    return svc.STT(
                        languages=[language],
                        api_key=os.getenv("GLADIA_API_KEY"),
                    )
                return gladia.STT(
                    languages=[language],
                    api_key=os.getenv("GLADIA_API_KEY"),
                )
            # Fallback to deepgram
            if provider not in (
                    "deepgram",
                    "openai",
                    "cartesia",
                    "lmnt",
                    "elevenlabs",
                    "playht",
                    "sarvam",
                    "google",
                    "aws",
                    "lmnt",
                    "elevenlabs",
                    "playht",
                    "sarvam",
                    "google",
                    "aws",
            ):
                self._logger.warning(
                    f"STT provider '{provider}' not available, using deepgram"
                )
            return deepgram.STT()

        except Exception as e:
            self._logger.error(f"Failed to create plugin STT ({provider}): {e}")
            return deepgram.STT()

    def _create_plugin_llm(self) -> Any:
        """Create LLM service using plugins with voice-optimized parameters."""
        if not _ensure_livekit_plugins_loaded(self._logger):
            raise RuntimeError(
                "LiveKit plugins must be initialized on the main thread."
            )
        cfg = self.llm_config
        provider = cfg.provider
        model = cfg.model
        parallel_tool_calls = cfg.parallel_tool_calls

        self.service_modes.llm_type = "plugin"

        # Get voice-optimized parameters with validation
        temperature = self._get_voice_optimized_temperature()
        max_tokens = self._get_voice_optimized_max_tokens()

        # Validate provider API key - fallback to OpenAI if missing
        is_valid, error_msg = self._validate_provider(provider)
        if not is_valid and provider != "openai":
            self._logger.warning(f"{error_msg}. Falling back to OpenAI.")
            # Check if OpenAI API key is available
            openai_valid, _ = self._validate_provider("openai")
            if openai_valid:
                return openai.LLM(
                    model="gpt-4o-mini",
                    temperature=temperature,
                    parallel_tool_calls=parallel_tool_calls,
                )
            else:
                # Last resort: try Groq
                self._logger.warning("OpenAI API key also missing, trying Groq")
                if groq:
                    return groq.LLM(
                        model="llama-3.1-8b-instant", temperature=temperature
                    )
                raise ValueError("No LLM provider API keys available")

        try:
            if provider == "openai":
                llm_kwargs = {
                    "model": model,
                    "temperature": temperature,
                    "parallel_tool_calls": parallel_tool_calls,
                }
                # Add prompt_cache_key for per-session caching (reduces token costs)
                if cfg.prompt_cache_key:
                    llm_kwargs["prompt_cache_key"] = cfg.prompt_cache_key
                # Add top_p for nucleus sampling control
                if cfg.top_p is not None:
                    llm_kwargs["top_p"] = cfg.top_p
                return openai.LLM(**llm_kwargs)
            elif provider == "groq" and groq:
                return groq.LLM(
                    model=model,
                    temperature=temperature,
                    parallel_tool_calls=parallel_tool_calls,
                )
            elif provider in ("gemini", "google") and google:
                self._logger.info(f"Creating Google LLM with model={model}")
                return google.LLM(model=model, temperature=temperature)
            elif provider == "anthropic":
                # LiveKit uses openai plugin for anthropic models via proxy
                return openai.LLM(
                    model=model,
                    temperature=temperature,
                    parallel_tool_calls=parallel_tool_calls,
                )
            elif provider == "cerebras":
                return openai.LLM.with_cerebras(
                    model=model,
                    api_key=os.getenv("CEREBRAS_API_KEY"),
                    temperature=temperature,
                )

            elif provider == "azure":
                azure_model = self.config.get(
                    "llm_model", os.getenv("AZURE_CHATGPT_MODEL")
                )
                azure_endpoint = (
                    self.config.get("azure_endpoint")
                    or self.config.get("endpoint")
                    or os.getenv("AZURE_BASE_URL")
                )
                azure_api_key = (
                    self.config.get("azure_api")
                    or os.getenv("AZURE_IN_API_KEY")
                )
                azure_api_version = (
                    self.config.get("azure_api_version")
                    or os.getenv("AZURE_OPENAI_VERSION", "2024-10-21")
                )
                missing = []
                if not azure_api_key:
                    missing.append("AZURE_IN_API_KEY")
                if not azure_endpoint:
                    missing.append("AZURE_BASE_URL")
                if not azure_model:
                    missing.append("AZURE_CHATGPT_MODEL")
                if missing:
                    self._logger.warning(
                        "Azure LLM config incomplete. Missing: "
                        + ", ".join(missing)
                        + ". Set env vars or provide config keys."
                    )
                self._logger.info(
                    f"Creating Azure LLM: model={azure_model}, "
                    f"endpoint={azure_endpoint}, "
                    f"api_version={azure_api_version}, "
                    f"api_key={'set' if azure_api_key else 'MISSING'}"
                )
                return openai.LLM.with_azure(
                    model=azure_model,
                    azure_endpoint=azure_endpoint,
                    api_key=azure_api_key,
                    api_version=azure_api_version,
                    temperature=temperature,
                )

            elif provider == "ollama":
                return openai.LLM.with_ollama(
                    model=self.config.get("llm_model", "llama3.2"),
                    base_url=self.config.get("llm_url", "http://localhost:11434"),
                    temperature=temperature,
                )
            elif provider == "aws":
                from livekit.plugins import aws

                # AWS Bedrock newer models require inference profiles
                # Map model IDs to global inference profile IDs
                AWS_INFERENCE_PROFILE_MAP = {
                    # Claude Haiku 4.5 - requires global inference profile
                    "anthropic.claude-haiku-4-5-20251001-v1:0": "global.anthropic.claude-haiku-4-5-20251001-v1:0",
                    # Claude 3.5 Haiku - requires global inference profile
                    "anthropic.claude-3-5-haiku-20241022-v1:0": "us.anthropic.claude-3-5-haiku-20241022-v1:0",
                    # Claude 3.5 Sonnet v2 requires cross-region profile
                    "anthropic.claude-3-5-sonnet-20241022-v2:0": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
                    # Claude 3.5 Sonnet requires cross-region profile
                    "anthropic.claude-3-5-sonnet-20240620-v1:0": "us.anthropic.claude-3-5-sonnet-20240620-v1:0",
                }

                # Check if model needs inference profile mapping
                inference_profile = self.config.get("aws_inference_profile")
                if inference_profile:
                    # Use explicit inference profile ARN from config
                    actual_model = inference_profile
                    self._logger.info(f"Using AWS inference profile: {actual_model}")
                elif model in AWS_INFERENCE_PROFILE_MAP:
                    # Map to global/cross-region inference profile
                    actual_model = AWS_INFERENCE_PROFILE_MAP[model]
                    self._logger.info(
                        f"AWS Bedrock: Mapped {model} to inference profile {actual_model}"
                    )
                else:
                    actual_model = model

                aws_region = self.config.get(
                    "aws_region", os.getenv("AWS_REGION", "ap-south-1")
                )
                return aws.LLM(
                    model=actual_model,
                    temperature=temperature,
                    region=aws_region,
                )
            elif provider == "xai":
                return openai.LLM.with_x_ai(
                    model=model,
                )
            elif provider == "qwen":
                # Qwen models via Cerbras AI API
                qwen_api_key = os.getenv("CEREBRAS_API_KEY")

                if not qwen_api_key:
                    self._logger.warning("CEREBRAS_API_KEY not set, using OpenAI fallback")
                    return openai.LLM(model="gpt-4o", temperature=temperature)

                return openai.LLM.with_cerebras(
                    model=model,
                    api_key=qwen_api_key,
                    temperature=temperature,
                )
            elif provider == "openrouter":
                # OpenAI models via OpenRouter API
                openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

                if not openrouter_api_key:
                    self._logger.warning("OPENROUTER_API_KEY not set, using OpenAI fallback")
                    return openai.LLM(model="gpt-4o", temperature=temperature)

                return openai.LLM(
                    model=model,
                    api_key=openrouter_api_key,
                    base_url="https://openrouter.ai/api/v1",
                    temperature=temperature,
                    parallel_tool_calls=parallel_tool_calls,
                )

            else:
                self._logger.warning(f"Unknown LLM provider '{provider}', using openai")
                return openai.LLM(model="gpt-4o", temperature=temperature)
        except Exception as e:
            self._logger.error(f"Failed to create plugin LLM ({provider}): {e}")
            return openai.LLM(model="gpt-4o-mini", temperature=0.4)

    def _create_plugin_tts(self) -> Any:
        """
        Create TTS service using plugins with provider-specific parameters.

        Supported providers (from LiveKit docs):
        - cartesia: speed, volume, emotion, language
        - openai: model, voice, instructions (gpt-4o-mini-tts only)
        - elevenlabs: voice_id, model, voice_settings (stability, similarity_boost, style, speed)
        - deepgram: model (includes voice, e.g., "aura-asteria-en")
        - google: language, gender, voice_name, credentials
        - aws: voice, speech_engine, language
        - azure: voice, language, prosody
        - lmnt: model, voice, language, temperature, top_p
        - groq: model, voice
        - playai: model, language, sample_rate
        - inworld: model, voice, language (via inference or plugin)
        """
        if not _ensure_livekit_plugins_loaded(self._logger):
            raise RuntimeError(
                "LiveKit plugins must be initialized on the main thread."
            )
        cfg = self.tts_config
        provider = cfg.provider

        self.service_modes.tts_type = "plugin"
        # Validate API key - fallback if missing
        is_valid, error_msg = self._validate_provider(provider)
        if not is_valid and provider != DEFAULT_TTS_PROVIDER:
            self._logger.warning(f"{error_msg}. Falling back to {DEFAULT_TTS_PROVIDER}.")
            return self._create_fallback_tts()

        try:
            # Dispatch to provider-specific creator
            creator = self._get_tts_creator(provider)
            if creator:
                return creator(cfg)

            self._logger.warning(f"TTS provider '{provider}' not available, using fallback")
            return self._create_fallback_tts()

        except Exception as e:
            self._logger.error(f"Failed to create plugin TTS ({provider}): {e}")
            return self._create_fallback_tts()

    def _get_tts_creator(self, provider: str):
        """Get the TTS creator function for a provider."""
        creators = {
            "cartesia": self._create_cartesia_tts,
            "openai": self._create_openai_tts,
            "elevenlabs": self._create_elevenlabs_tts,
            "deepgram": self._create_deepgram_tts,
            "google": self._create_google_tts,
            "gemini": self._create_gemini_tts,
            "aws": self._create_aws_tts,
            "azure": self._create_azure_tts,
            "lmnt": self._create_lmnt_tts,
            "groq": self._create_groq_tts,
            "playht": self._create_playai_tts,
            "playai": self._create_playai_tts,
            "inworld": self._create_inworld_tts,
            "sarvam": self._create_sarvam_tts,
        }
        return creators.get(provider)

    # =========================================================================
    # Provider-Specific TTS Creators
    # =========================================================================

    def _create_cartesia_tts(self, cfg: TTSConfig) -> Any:
        """
        Cartesia TTS - high quality with speed/emotion control.

        Docs: https://docs.livekit.io/agents/models/tts/plugins/cartesia/
        Params: model, voice, language, emotion, speed (0.6-2.0), volume
        """
        if not cartesia:
            raise ImportError("Cartesia plugin not available")

        return cartesia.TTS(
            model=cfg.model or "sonic-3",
            voice=cfg.voice,
            language=cfg.language,
            speed=max(0.6, min(1.5, cfg.speed)),
        )

    def _create_openai_tts(self, cfg: TTSConfig) -> Any:
        """
        OpenAI TTS - supports instructions for gpt-4o-mini-tts.

        Docs: https://docs.livekit.io/agents/models/tts/plugins/openai/
        Params: model, voice, instructions (gpt-4o-mini-tts only)
        Note: LiveKit plugin does NOT support speed parameter per docs.
        """
        voice = self._validate_openai_voice(cfg.voice)
        model = self._validate_openai_tts_model(cfg.model)

        # Only gpt-4o-mini-tts supports instructions
        if model == "gpt-4o-mini-tts" and cfg.voice_instructions:
            return openai.TTS(
                model=model,
                voice=voice,
                instructions=cfg.voice_instructions,
            )

        if cfg.voice_instructions and model != "gpt-4o-mini-tts":
            self._logger.warning(
                f"TTS model '{model}' doesn't support voice_instructions. "
                "Use 'gpt-4o-mini-tts' for instruction support."
            )

        return openai.TTS(model=model, voice=voice)

    def _create_elevenlabs_tts(self, cfg: TTSConfig) -> Any:
        """
        ElevenLabs TTS - rich voice settings control.

        Docs: https://docs.livekit.io/agents/models/tts/plugins/elevenlabs/
        Params: voice_id, model, language, streaming_latency, voice_settings
        voice_settings: stability, similarity_boost, style, use_speaker_boost, speed
        """
        if not elevenlabs:
            raise ImportError("ElevenLabs plugin not available")

        kwargs: dict[str, Any] = {
            "voice_id": cfg.voice,
            "model": cfg.model or "eleven_flash_v2_5",
            "language": cfg.language,
            "enable_ssml_parsing": True,
        }

        # Build VoiceSettings dataclass if any parameters provided.
        # The plugin expects elevenlabs.VoiceSettings, not a plain dict.
        has_settings = (
            cfg.stability is not None
            or cfg.similarity_boost is not None
            or cfg.style is not None
            or cfg.use_speaker_boost is not None
            or cfg.speed != 1.0
        )
        if has_settings:
            vs_kwargs: dict[str, Any] = {
                "stability": cfg.stability if cfg.stability is not None else 0.5,
                "similarity_boost": (
                    cfg.similarity_boost
                    if cfg.similarity_boost is not None
                    else 0.75
                ),
            }
            if cfg.style is not None:
                vs_kwargs["style"] = cfg.style
            if cfg.use_speaker_boost is not None:
                vs_kwargs["use_speaker_boost"] = cfg.use_speaker_boost
            if cfg.speed != 1.0:
                vs_kwargs["speed"] = cfg.speed
            kwargs["voice_settings"] = elevenlabs.VoiceSettings(**vs_kwargs)

        # DIAGNOSTIC: Log exact parameters for debugging TTS creation
        api_key_set = bool(os.getenv("ELEVENLABS_API_KEY"))
        self._logger.info(
            f"[ELEVENLABS_DIAG] Creating TTS with: "
            f"voice_id={cfg.voice!r}, model={kwargs['model']!r}, "
            f"language={cfg.language!r}, "
            f"has_voice_settings={has_settings}, "
            f"ELEVENLABS_API_KEY={'SET' if api_key_set else 'MISSING'}, "
            f"stability={cfg.stability}, similarity_boost={cfg.similarity_boost}, "
            f"style={cfg.style}, speed={cfg.speed}"
        )

        return elevenlabs.TTS(**kwargs)

    def _create_deepgram_tts(self, cfg: TTSConfig) -> Any:
        """
        Deepgram TTS - model includes voice (e.g., "aura-asteria-en").

        Docs: https://docs.livekit.io/agents/models/tts/plugins/deepgram/
        Params: model (default: aura-asteria-en)
        """
        # Deepgram model names include voice (e.g., "aura-asteria-en")
        model = cfg.model or "aura-asteria-en"
        return deepgram.TTS(model=model)

    def _create_google_tts(self, cfg: TTSConfig) -> Any:
        """
        Google TTS - auto-detects Gemini TTS vs Google Cloud TTS by model name.

        Routes to Gemini TTS for gemini-*/chirp-* models, otherwise Google Cloud TTS.
        """
        if not google:
            raise ImportError("Google plugin not available")

        model_lower = (cfg.model or "").lower()
        if model_lower.startswith("gemini-") or model_lower.startswith("chirp"):
            return self._create_gemini_tts(cfg)

        # Google Cloud TTS - legacy path
        lang_map = {
            "hi": "hi-IN", "ta": "ta-IN", "te": "te-IN", "kn": "kn-IN",
            "ml": "ml-IN", "mr": "mr-IN", "bn": "bn-IN", "gu": "gu-IN",
            "pa": "pa-IN", "en": "en-US", "en-us": "en-US", "en-gb": "en-GB",
        }
        language = lang_map.get(cfg.language.lower(), cfg.language)

        return google.TTS(
            language=language,
            gender=cfg.gender,
            voice_name=cfg.voice if cfg.voice else None,
            credentials_file=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
        )

    def _create_gemini_tts(self, cfg: TTSConfig) -> Any:
        """
        Gemini TTS - AI-native speech generation with instruction control.

        Docs: https://docs.livekit.io/agents/models/tts/plugins/gemini/
        Params: model, voice_name, instructions
        Models: gemini-2.5-flash-preview-tts, chirp-3.0-generate-001
        Voices: Puck, Charon, Kore, Fenrir, Aoede, Leda, Orus, Zephyr, Achernar
        """
        if not google:
            raise ImportError("Google plugin not available")

        model = cfg.model or "gemini-2.5-flash-preview-tts"
        voice = self._common.validate_gemini_realtime_voice(
            cfg.voice, default="Kore"
        )

        kwargs: Dict[str, Any] = {
            "model": model,
            "voice_name": voice,
        }

        if cfg.voice_instructions:
            kwargs["instructions"] = cfg.voice_instructions

        self._logger.info(
            f"Creating Gemini TTS: model={model}, voice={voice}"
        )

        return google.beta.GeminiTTS(**kwargs)

    def _create_aws_tts(self, cfg: TTSConfig) -> Any:
        """
        AWS Polly TTS - supports multiple speech engines.

        Docs: https://docs.livekit.io/agents/models/tts/plugins/aws/
        Params: voice, language, speech_engine (standard/neural/long-form/generative)
        """
        svc = self._lazy_import_plugin("aws")
        if not svc:
            raise ImportError("AWS plugin not available")

        aws_region = self.config.get(
            "aws_region", os.getenv("AWS_REGION", "ap-south-1")
        )
        return svc.TTS(
            voice=cfg.voice or "Ruth",
            language=cfg.language,
            speech_engine=cfg.speech_engine,
            region=aws_region,
        )

    def _create_azure_tts(self, cfg: TTSConfig) -> Any:
        """
        Azure Speech TTS - requires speech_key and speech_region.

        Docs: https://docs.livekit.io/agents/models/tts/plugins/azure/
        Params: voice, language, speech_key, speech_region
        """
        from livekit.plugins import openai

        return azure.TTS(
            voice=cfg.voice,
            language=cfg.language,
            speech_key=os.getenv("AZURE_SPEECH_KEY"),
            speech_region=os.getenv("AZURE_SPEECH_REGION"),
        )

    def _create_lmnt_tts(self, cfg: TTSConfig) -> Any:
        """
        LMNT TTS - supports temperature and top_p for expressiveness.

        Docs: https://docs.livekit.io/agents/models/tts/plugins/lmnt/
        Params: model (blizzard/aurora), voice, language, temperature, top_p
        Note: Does NOT support speed or sample_rate per docs.
        """
        svc = self._lazy_import_plugin("lmnt")
        if not svc:
            from livekit.plugins import lmnt as svc

        model = cfg.model or "blizzard"
        voice = cfg.voice or "leah"

        # Warn if voice looks like UUID (wrong provider)
        if self._looks_like_uuid(voice):
            self._logger.warning(f"LMNT voice '{voice}' looks like UUID. Using 'leah'")
            voice = "leah"

        kwargs = {
            "model": model,
            "voice": voice,
            "language": cfg.language,
        }

        # Add optional parameters if set
        if cfg.temperature is not None:
            kwargs["temperature"] = cfg.temperature
        if cfg.top_p is not None:
            kwargs["top_p"] = cfg.top_p

        return svc.TTS(**kwargs)

    def _create_groq_tts(self, cfg: TTSConfig) -> Any:
        """
        Groq TTS - PlayAI-based, fast inference.

        Docs: https://docs.livekit.io/agents/models/tts/plugins/groq/
        Params: model (default: playai-tts), voice (default: Arista-PlayAI)
        """
        if not groq:
            raise ImportError("Groq plugin not available")

        return groq.TTS(
            model=cfg.model or "playai-tts",
            voice=cfg.voice or "Arista-PlayAI",
        )

    def _create_playai_tts(self, cfg: TTSConfig) -> Any:
        """
        PlayAI/PlayHT TTS - requires user_id and api_key.

        Params: model (default: Play3.0-mini), language, sample_rate
        """
        svc = self._lazy_import_plugin("playai")
        if not svc:
            raise ImportError("PlayAI plugin not available")

        return svc.TTS(
            model=cfg.model or "Play3.0-mini",
            language=cfg.language or "english",
            sample_rate=cfg.sample_rate,
        )

    def _create_inworld_tts(self, cfg: TTSConfig) -> Any:
        """
        Inworld TTS - can use plugin or inference mode.

        Params: model, voice, temperature, speaking_rate
        """
        # Try plugin first
        try:
            from livekit.plugins import inworld

            self._logger.info(
                f"Creating Inworld TTS: model={cfg.model}, voice={cfg.voice}"
            )

            return inworld.TTS(
                model=cfg.model,
                voice=cfg.voice,
                temperature=cfg.temperature,
                speaking_rate=cfg.speed if cfg.speed != 1.0 else None,
            )
        except ImportError:
            # Fall back to inference mode with extra_kwargs
            self._logger.info("Inworld plugin not available, using inference mode")
            extra_kwargs = self._build_inference_tts_extra_kwargs("inworld", cfg)
            return inference.TTS(
                model=f"inworld/{cfg.model}",
                voice=cfg.voice,
                language=cfg.language,
                extra_kwargs=extra_kwargs if extra_kwargs else None,
            )

    def _create_sarvam_tts(self, cfg: TTSConfig) -> Any:
        """
        Sarvam TTS - Indian language specialist.

        Params: target_language_code, speaker, pitch, pace, loudness
        """
        svc = self._lazy_import_plugin("sarvam")
        if not svc:
            raise ImportError("Sarvam plugin not available")

        # Map language codes to Sarvam format
        lang_map = {
            "hi": "hi-IN", "ta": "ta-IN", "te": "te-IN", "kn": "kn-IN",
            "ml": "ml-IN", "mr": "mr-IN", "bn": "bn-IN", "gu": "gu-IN",
            "pa": "pa-IN", "en": "en-IN",
        }
        target_language = lang_map.get(cfg.language.lower(), "hi-IN")

        return svc.TTS(
            target_language_code=target_language,
            speaker=cfg.voice,
            pitch=cfg.pitch,
            pace=cfg.pace,
            loudness=cfg.loudness,
        )

    def _validate_deepgram_voice(self, voice: str) -> str:
        """Validate and return a valid Deepgram TTS voice."""
        voice_lower = voice.lower()
        if voice_lower in DEEPGRAM_TTS_VOICES:
            return voice_lower

        # Check if this looks like a UUID (wrong provider/voice combo)
        if self._looks_like_uuid(voice):
            self._logger.warning(
                f"Voice '{voice}' looks like a UUID but Deepgram TTS "
                f"requires voice names. Using default: {INFERENCE_TTS_DEFAULT_VOICES['deepgram']}"
            )
            return INFERENCE_TTS_DEFAULT_VOICES["deepgram"]

        self._logger.warning(
            f"Voice '{voice}' is not a known Deepgram voice. "
            f"Using default: {INFERENCE_TTS_DEFAULT_VOICES['deepgram']}"
        )
        return INFERENCE_TTS_DEFAULT_VOICES["deepgram"]

    def _validate_openai_voice(
            self, voice: str, default: str = "alloy", log_warning: bool = True
    ) -> str:
        """Validate and return a valid OpenAI TTS voice."""
        return self._common.validate_openai_voice(
            voice, default=default, log_warning=log_warning
        )

    def _validate_openai_tts_model(self, model: str, default: str = "tts-1") -> str:
        """Validate and return a valid OpenAI TTS model."""
        return self._common.validate_openai_tts_model(model, default=default)

    def _create_fallback_tts(self) -> Any:
        """Create fallback TTS using default provider configuration."""
        fallback_model = os.getenv("FALLBACK_TTS_MODEL", DEFAULT_TTS_MODEL)
        fallback_voice = os.getenv("FALLBACK_TTS_VOICE", DEFAULT_TTS_VOICE)
        self._logger.warning(
            f"Using fallback TTS: {DEFAULT_TTS_PROVIDER} {fallback_model}"
        )

        # Try to create TTS with the default provider
        try:
            return inference.TTS(
                model=f"{DEFAULT_TTS_PROVIDER}/{fallback_model}",
                voice=fallback_voice,
            )
        except Exception as e:
            self._logger.warning(f"Default TTS failed: {e}. Using OpenAI tts-1")
            return openai.TTS(model="tts-1", voice="alloy")

    # =========================================================================
    # Session Creation
    # =========================================================================

    async def create_session(
            self,
            userdata: Optional[Dict[str, Any]] = None,
            mode: Optional[str] = None,
            user_state=None,
    ) -> AgentSession:
        """
        Create an AgentSession with unified service creation.

        For inference/standard modes, uses create_stt/llm/tts() which
        automatically select inference vs plugin based on priority logic.

        For realtime mode, uses native realtime models (OpenAI, Gemini).

        Args:
            userdata: Optional userdata to attach to session
            mode: Override mode (inference/realtime/standard)

        Returns:
            Configured AgentSession
        """
        start = perf_counter()
        effective_mode = mode or self.mode
        userdata = userdata or {}

        # Create VAD (common to all modes)
        vad = self._create_vad()

        # Realtime mode uses different classes (OpenAI/Gemini realtime)
        if effective_mode == LiveKitServiceMode.REALTIME or self.config.get("llm_realtime"):
            return await self._create_realtime_session(userdata, vad)

        self._logger.info(
            f"[TIMING] session event start till vad  {((perf_counter() - start) * 1000):.0f}ms"
        )

        # Inference and Standard modes use unified service creation
        # Create all services in parallel for faster startup
        services_creation = perf_counter()
        stt, llm, tts = await asyncio.gather(
            self.create_stt_with_retry(),
            self.create_llm_with_retry(),
            self.create_tts_with_retry(),
        )

        # Only store service_modes in extra_data for inference mode
        if user_state and effective_mode == LiveKitServiceMode.INFERENCE:
            if not isinstance(user_state.extra_data, dict):
                user_state.extra_data = {}
            user_state.extra_data['service_modes'] = self.service_modes

        services_creation = (perf_counter() - services_creation) * 1000
        if user_state:
            add_perf_log(user_state, "stt_llm_tts_creation", services_creation)

        self._logger.info(
            f"[TIMING] stt,tts,llm services creation {services_creation:.0f}ms"
        )

        extra_printing = perf_counter()
        # Log provider and model names from created services
        stt_info = (
                getattr(stt, "model", None)
                or f"{type(stt).__module__}/{type(stt).__name__}"
        )
        llm_info = (
                getattr(llm, "model", None)
                or f"{type(llm).__module__}/{type(llm).__name__}"
        )
        tts_info = (
                getattr(tts, "model", None)
                or f"{type(tts).__module__}/{type(tts).__name__}"
        )

        self._logger.info(
            f"Creating session (mode={effective_mode}):\n"
            f"  STT: {stt_info}\n"
            f"  LLM: {llm_info}\n"
            f"  TTS: {tts_info}"
        )

        self._logger.info(
            f"[TIMING] extra prints {((perf_counter() - extra_printing) * 1000):.0f}ms"
        )

        session_kwargs = {
            "userdata": userdata,
            "stt": stt,
            "llm": llm,
            "tts": tts,
            "vad": vad,
            "min_interruption_duration": self.speaking_plan.get(
                "min_interruption_duration", 0.3
            ),
            "min_interruption_words": self.speaking_plan.get(
                "min_interruption_words", 3
            ),
            # Endpointing delay: time after last speech before declaring turn complete
            # Default 0.5s is conservative; 0.3s gives faster response at slight accuracy cost
            # Turn detector model dynamically adjusts between min and max
            "min_endpointing_delay": self.speaking_plan.get("min_endpointing_delay", 0.3),
            "max_endpointing_delay": self.speaking_plan.get("max_endpointing_delay", 2.0),
            # IMPORTANT: preemptive_generation=False to prevent duplicate LLM requests/TTS
            # See: https://github.com/livekit/agents/issues/4219
            # When True, causes duplicate audio output and doubled token costs
            "preemptive_generation": self.speaking_plan.get("preemptive_generation", True),
            # Resume after false interruptions for better conversation flow
            "resume_false_interruption": self.speaking_plan.get("resume_false_interruption", True),
            "false_interruption_timeout": self.speaking_plan.get("false_interruption_timeout", 0.3),
        }

        # MultilingualModel requires downloaded model files
        # Only enable if config allows and model files are available
        multilingual_detection = perf_counter()
        use_multilingual = self.config.get("use_multilingual_turn_detection", True)
        if use_multilingual and MultilingualModel:
            try:
                session_kwargs["turn_detection"] = MultilingualModel()
            except RuntimeError as e:
                if "languages.json" in str(e):
                    self._logger.warning(
                        "MultilingualModel unavailable - model files not downloaded. "
                        "Run `python3 -m livekit.agents download-files` to enable."
                    )
                else:
                    raise

        self._logger.info(
            f"[TIMING] multilingual detection {((perf_counter() - multilingual_detection) * 1000):.0f}ms"
        )

        return AgentSession(**session_kwargs)

    async def create_text_session(
            self,
            userdata: Optional[Dict[str, Any]] = None,
            mode: Optional[str] = None,
    ) -> AgentSession:
        """
        Create an AgentSession for text-only (hybrid) mode.

        Per LiveKit docs: https://docs.livekit.io/agents/build/text/
        Text-only mode is configured via RoomOptions(audio_input=False, audio_output=False)
        at session.start() time, not by omitting STT/TTS from the session.

        The AgentSession still needs STT/TTS components, but they won't be used
        when audio is disabled via RoomOptions. This prevents assertion errors
        when generate_reply() is called.

        Args:
            userdata: Optional userdata to attach to session
            mode: Override mode (inference/realtime/standard)

        Returns:
            Configured AgentSession (audio disabled via RoomOptions at start time)
        """
        effective_mode = mode or self.mode
        userdata = userdata or {}

        self._logger.info(
            f"Creating session for TEXT-ONLY mode (mode={effective_mode}). "
            "Audio will be disabled via RoomOptions at start time."
        )

        # Create LLM (required for all modes)
        llm = await self.create_llm_with_retry()

        # Log LLM info
        llm_info = (
                getattr(llm, "model", None)
                or f"{type(llm).__module__}/{type(llm).__name__}"
        )
        self._logger.info(f"Text session LLM: {llm_info}")

        # Create VAD for presence detection
        vad = self._create_vad()

        # For text-only mode, we still create STT/TTS but they won't be used
        # because RoomOptions(audio_input=False, audio_output=False) is set
        # This prevents "tts_node called but no TTS node is available" errors
        stt = await self.create_stt_with_retry()
        tts = await self.create_tts_with_retry()

        session_kwargs = {
            "userdata": userdata,
            "llm": llm,
            "vad": vad,
            "stt": stt,
            "tts": tts,
            # IMPORTANT: preemptive_generation=False to prevent duplicate LLM requests/TTS
            # See: https://github.com/livekit/agents/issues/4219
            "preemptive_generation": False,
        }

        return AgentSession(**session_kwargs)

    def _create_vad(self) -> Any:
        """Create Silero VAD with configured settings."""
        if not _ensure_livekit_plugins_loaded(self._logger):
            raise RuntimeError(
                "LiveKit plugins must be initialized on the main thread."
            )

        return silero.VAD.load(
            min_silence_duration=self.speaking_plan.get("min_silence_duration", 0.10),  # Reduced from 1.5 for faster EOU detection
            prefix_padding_duration=self.speaking_plan.get("prefix_padding_duration", 0.05),  # Reduced from 0.08 to reduce audio buffering delay
            activation_threshold=self.speaking_plan.get("vad_activation_threshold", 0.60),  # Higher threshold = less sensitive to background noise
            deactivation_threshold=self.speaking_plan.get("vad_deactivation_threshold", 0.25),
            sample_rate=self.speaking_plan.get("vad_sample_rate", 8000),
        )

    def create_background_audio(self) -> Optional[Any]:
        """
        Create BackgroundAudioPlayer with configured ambient and thinking sounds.

        Background audio makes the agent feel more realistic by playing:
        - Ambient sound: Continuous background noise (e.g., office ambience)
        - Thinking sound: Played when agent is processing (e.g., keyboard typing)

        Config options:
        - background_audio.enabled: Enable/disable background audio
          (default: True for telephony calls, False otherwise)
        - background_audio.ambient_sound: BuiltinAudioClip name or file path
        - background_audio.ambient_volume: Volume 0.0-1.0 (default: 0.8)
        - background_audio.thinking_sound: BuiltinAudioClip name(s) or file path(s)
        - background_audio.thinking_volume: Volume 0.0-1.0 (default: 0.7)

        Returns:
            BackgroundAudioPlayer instance if enabled and available, None otherwise
        """
        if BackgroundAudioPlayer is None:
            self._logger.debug(
                "BackgroundAudioPlayer not available in this LiveKit version"
            )
            return None

        bg_config = self.config.get("background_audio", {})

        # Enable background audio by default for telephony (SIP) calls
        call_type = self.config.get("call_type", "")
        is_telephony = call_type in ("outbound", "inbound")
        _enabled = bg_config.get("enabled", is_telephony)  # Reserved for future use

        try:
            # Get ambient sound configuration
            # Use pipecat's office ambience MP3 file as default instead of builtin clip
            default_ambient_sound = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "assets",
                "examples_foundational_assets_office-ambience-24000-mono.mp3",
            )
            ambient_sound_config = bg_config.get("ambient_sound", default_ambient_sound)
            ambient_sound = self._resolve_audio_config(
                ambient_sound_config,
                bg_config.get("ambient_volume", 0.1),  # Reduced to 10%
            )

            # Get thinking sound configuration (can be a list)
            thinking_sound_config = bg_config.get(
                "thinking_sound", ["KEYBOARD_TYPING", "KEYBOARD_TYPING2"]
            )
            thinking_volume = bg_config.get(
                "thinking_volume", 0.1
            )  # Reduced from 0.7 to 0.1

            if isinstance(thinking_sound_config, list):
                thinking_sounds = [
                    self._resolve_audio_config(sound, thinking_volume)
                    for sound in thinking_sound_config
                ]
            else:
                thinking_sounds = [
                    self._resolve_audio_config(thinking_sound_config, thinking_volume)
                ]

            self._logger.info(
                f"Creating BackgroundAudioPlayer (ambient={ambient_sound_config}, "
                f"thinking={thinking_sound_config})"
            )

            return BackgroundAudioPlayer(
                ambient_sound=ambient_sound,
                thinking_sound=thinking_sounds,
            )

        except Exception as e:
            self._logger.warning(f"Failed to create BackgroundAudioPlayer: {e}")
            return None

    def _resolve_audio_config(self, sound: str, volume: float) -> Optional[Any]:
        """
        Resolve audio configuration from string to AudioConfig.

        Args:
            sound: BuiltinAudioClip name (e.g., "OFFICE_AMBIENCE") or file path
            volume: Volume level 0.0-1.0

        Returns:
            AudioConfig instance
        """
        if AudioConfig is None or BuiltinAudioClip is None:
            return None

        # Check if it's a builtin clip name
        if hasattr(BuiltinAudioClip, sound.upper()):
            clip = getattr(BuiltinAudioClip, sound.upper())
            return AudioConfig(clip, volume=volume)

        # Assume it's a file path
        return AudioConfig(sound, volume=volume)

    # =========================================================================
    # Realtime Session Creation
    # =========================================================================

    async def _create_realtime_session(
            self,
            userdata: Dict[str, Any],
            vad: Any,
    ) -> AgentSession:
        """
        Create session using realtime mode (native realtime models).

        Realtime mode uses native realtime APIs with integrated audio:
        - OpenAI Realtime: openai.realtime.RealtimeModel()
        - Gemini Realtime: google.realtime.RealtimeModel()
        - Azure Realtime: openai.realtime.RealtimeModel.with_azure()
        - XAI Realtime: xai.realtime.RealtimeModel()

        Features:
        - Voice/model validation
        - Turn detection configuration
        - Mixed realtime mode (text output for separate TTS)
        - System instructions support

        Supported llm_provider values:
        - "openai-realtime" or "openai" with realtime model
        - "gemini-realtime", "google-realtime"
        - "azure-realtime"
        - "xai-realtime"
        """
        llm_provider = self.config.get("llm_provider", "openai-realtime").lower()
        llm_model = self.config.get("llm_model", "")

        # Auto-detect realtime mode from model name using the imported function
        model_is_realtime = is_realtime_model(llm_model)

        if not model_is_realtime:
            model_is_realtime = self.config.get("llm_realtime", False)

        # Check for mixed realtime mode
        mixed_realtime_mode = self.config.get(
            "mixed_realtime_mode",
            os.getenv("MIXED_REALTIME_MODE", "false").lower() == "true",
        )

        self._logger.info(
            f"Creating realtime session - provider: {llm_provider}, "
            f"model: {llm_model}, mixed_mode: {mixed_realtime_mode}"
        )

        # Route to appropriate realtime session creator
        if llm_provider == "openai-realtime" or (
                llm_provider == "openai" and model_is_realtime
        ):
            return self._create_openai_realtime_session(userdata, vad)

        elif llm_provider in ("gemini-realtime", "google-realtime", "google", "gemini") or (
                llm_provider in ("google", "gemini") and model_is_realtime
        ):
            return self._create_gemini_realtime_session(userdata, vad)

        elif llm_provider == "xai-realtime" or (
                llm_provider == "xai" and model_is_realtime
        ):
            return self._create_xai_realtime_session(userdata, vad)

        elif llm_provider == "azure-realtime":
            return self._create_azure_realtime_session(userdata, vad)

        else:
            self._logger.warning(
                f"Unknown realtime provider '{llm_provider}', "
                "falling back to standard session"
            )
            # Fall back to standard session creation
            return await self.create_session(userdata, mode=LiveKitServiceMode.STANDARD)

    def _create_xai_realtime_session(
            self, userdata: Dict[str, Any], vad: Any
    ) -> AgentSession:
        """
        Create XAI (Grok) Realtime Session with enhanced configuration.

        Features:
        - Mixed realtime mode support
        - System instructions
        """
        if not xai:
            self._logger.error(
                "XAI plugin not available. "
                "Install with: pip install 'livekit-plugins-xai'"
            )
            raise ImportError("XAI plugin not available")

        model = self.config.get("llm_model", "grok-2-voice")
        voice = self.config.get("tts_voice", "ara")
        instructions = self.config.get("system_prompt", "")

        # Check for mixed realtime mode
        mixed_realtime_mode = self.config.get(
            "mixed_realtime_mode",
            os.getenv("MIXED_REALTIME_MODE", "false").lower() == "true",
        )

        # Log mode
        if mixed_realtime_mode:
            self._logger.info(
                "🔀 Mixed Realtime Mode: XAI text output for separate TTS"
            )
        else:
            self._logger.info(
                "⚡ Full Realtime Mode: XAI Grok (integrated audio)"
            )

        self._logger.info(
            f"Creating XAI Realtime session - model: {model}, voice: {voice}"
        )

        # Build RealtimeModel kwargs
        realtime_kwargs: Dict[str, Any] = {
            "voice": voice,
            "model": model,
        }

        if instructions:
            realtime_kwargs["instructions"] = instructions

        llm_model = xai.realtime.RealtimeModel(**realtime_kwargs)

        # Build session kwargs
        session_kwargs: Dict[str, Any] = {
            "userdata": userdata,
            "llm": llm_model,
            "vad": vad,
        }

        # Always add TTS for session.say() functionality
        tts = self.create_tts()
        session_kwargs["tts"] = tts
        if mixed_realtime_mode:
            self._logger.info("Mixed mode: TTS handles all speech output")
        else:
            self._logger.info("Full realtime mode: TTS added for session.say() calls")

        return AgentSession(**session_kwargs)

    def _create_azure_realtime_session(
            self, userdata: Dict[str, Any], vad: Any
    ) -> AgentSession:
        """
        Create Azure Realtime Session with enhanced configuration.

        Features:
        - Voice validation
        - Turn detection
        - Mixed realtime mode support
        - System instructions
        """
        model = self.config.get("llm_model", os.getenv("AZURE_CHATGPT_MODEL"))

        # Validate voice (Azure uses OpenAI voices)
        voice = self.config.get("tts_voice", "alloy")
        voice = self._common.validate_openai_realtime_voice(voice)

        temperature = self.config.get("temperature", 0.7)
        instructions = self.config.get("system_prompt", "")

        azure_endpoint = self.config.get(
            "azure_endpoint", os.getenv("AZURE_REALTIME_ENDPOINT")
        )
        azure_deployment = model
        azure_api = self.config.get("azure_api", os.getenv("AZURE_IN_API_KEY"))
        azure_api_version = self.config.get(
            "azure_api_version", os.getenv("AZURE_OPENAI_VERSION", "2024-10-01-preview")
        )

        # Check for mixed realtime mode
        mixed_realtime_mode = self.config.get(
            "mixed_realtime_mode",
            os.getenv("MIXED_REALTIME_MODE", "false").lower() == "true",
        )

        # Build turn detection configuration
        turn_detection_enabled = self.config.get("turn_detection", True)
        turn_detection = None
        if turn_detection_enabled and TurnDetection:
            turn_detection_type = self.speaking_plan.get("turn_detection_type", "semantic_vad")
            if turn_detection_type == "server_vad":
                # Server VAD: uses threshold-based voice activity detection
                turn_detection = TurnDetection(
                    type="server_vad",
                    threshold=self.speaking_plan.get("vad_threshold", 0.4),
                    silence_duration_ms=int(self.speaking_plan.get("vad_silence_threshold_secs", 0.6) * 1000),
                    create_response=True,
                    interrupt_response=True,
                )
            else:
                # Semantic VAD: uses LLM-based turn detection
                turn_detection = TurnDetection(
                    type="semantic_vad",
                    eagerness=self.speaking_plan.get("eagerness", "medium"),
                    create_response=True,
                    interrupt_response=True,
                )

        # Log mode
        if mixed_realtime_mode:
            self._logger.info(
                "🔀 Mixed Realtime Mode: Azure text output for separate TTS"
            )
        else:
            self._logger.info(
                "⚡ Full Realtime Mode: Azure (integrated audio)"
            )

        self._logger.info(
            f"Creating Azure Realtime session - model: {model}, voice: {voice}, "
            f"endpoint: {azure_endpoint}"
        )

        # Build RealtimeModel kwargs
        realtime_kwargs: Dict[str, Any] = {
            "azure_endpoint": azure_endpoint,
            "azure_deployment": azure_deployment,
            "voice": voice,
            "api_key": azure_api,
            "api_version": azure_api_version,
            "temperature": temperature,
        }

        if turn_detection:
            realtime_kwargs["turn_detection"] = turn_detection

        if instructions:
            realtime_kwargs["instructions"] = instructions

        llm_model = openai.realtime.RealtimeModel.with_azure(**realtime_kwargs)

        # Build session kwargs
        session_kwargs: Dict[str, Any] = {
            "userdata": userdata,
            "llm": llm_model,
            "vad": vad,
        }

        # Always add TTS for session.say() functionality
        tts = self.create_tts()
        session_kwargs["tts"] = tts
        if mixed_realtime_mode:
            self._logger.info("Mixed mode: TTS handles all speech output")
        else:
            self._logger.info("Full realtime mode: TTS added for session.say() calls")

        return AgentSession(**session_kwargs)

    def _create_openai_realtime_session(
            self,
            userdata: Dict[str, Any],
            vad: Any,
    ) -> AgentSession:
        """
        Create OpenAI Realtime session with enhanced configuration.

        Features:
        - Voice/model validation
        - Turn detection with semantic VAD
        - Tool calling support
        - Mixed realtime mode (text output for separate TTS)
        - Audio input configuration (noise reduction, transcription)
        """
        # Get and validate model - default to gpt-realtime per LiveKit docs
        model = self.config.get("llm_model", "gpt-realtime")
        model = self._common.validate_openai_realtime_model(model, default="gpt-realtime")

        # Get and validate voice
        voice = self.config.get("tts_voice", "alloy")
        voice = self._common.validate_openai_realtime_voice(voice)

        temperature = self.config.get("temperature", 0.7)
        instructions = self.config.get("system_prompt", "")

        # Check for mixed realtime mode (text output for separate TTS)
        mixed_realtime_mode = self.config.get(
            "mixed_realtime_mode",
            os.getenv("MIXED_REALTIME_MODE", "false").lower() == "true",
        )

        # Build turn detection configuration
        turn_detection_enabled = self.config.get("turn_detection", True)
        turn_detection = None
        if turn_detection_enabled and TurnDetection:
            turn_detection_type = self.speaking_plan.get("turn_detection_type", "semantic_vad")
            if turn_detection_type == "server_vad":
                # Server VAD: uses threshold-based voice activity detection
                turn_detection = TurnDetection(
                    type="server_vad",
                    threshold=self.speaking_plan.get("vad_threshold", 0.4),
                    silence_duration_ms=int(self.speaking_plan.get("vad_silence_threshold_secs", 0.6) * 1000),
                    create_response=True,
                    interrupt_response=True,
                )
            else:
                # Semantic VAD: uses LLM-based turn detection
                turn_detection = TurnDetection(
                    type="semantic_vad",
                    eagerness=self.speaking_plan.get("eagerness", "medium"),
                    create_response=True,
                    interrupt_response=True,
                )

        # Build modalities based on mode
        # Mixed mode: ["text"] for separate TTS
        # Full realtime: ["audio", "text"] or let default
        modalities = None
        if mixed_realtime_mode:
            modalities = ["text"]
            self._logger.info(
                "🔀 Mixed Realtime Mode: output_modalities=['text'] for separate TTS"
            )
        else:
            self._logger.info(
                "⚡ Full Realtime Mode: OpenAI Realtime (integrated audio)"
            )

        self._logger.info(
            f"Creating OpenAI Realtime session - model: {model}, voice: {voice}, "
            f"turn_detection: {turn_detection_enabled}, mixed_mode: {mixed_realtime_mode}"
        )

        # Build RealtimeModel kwargs
        # Note: OpenAI RealtimeModel does NOT accept 'instructions' parameter
        # System instructions are handled through chat context, not model init
        realtime_kwargs: Dict[str, Any] = {
            "model": model,
            "voice": voice,
        }

        if turn_detection:
            realtime_kwargs["turn_detection"] = turn_detection

        if modalities:
            realtime_kwargs["modalities"] = modalities

        # Create the RealtimeModel
        llm_model = openai.realtime.RealtimeModel(**realtime_kwargs)

        # Build session kwargs
        session_kwargs: Dict[str, Any] = {
            "userdata": userdata,
            "llm": llm_model,
            "vad": vad,
        }

        # Only add TTS in mixed mode - full realtime uses native audio
        if mixed_realtime_mode:
            tts = self.create_tts()
            session_kwargs["tts"] = tts
            self._logger.info("Mixed mode: TTS handles all speech output")
        else:
            self._logger.info("Full realtime mode: LLM handles audio natively (no TTS)")

        return AgentSession(**session_kwargs)

    def _create_gemini_realtime_session(
            self,
            userdata: Dict[str, Any],
            vad: Any,
    ) -> AgentSession:
        """
        Create Gemini Realtime session with enhanced configuration.

        Reference: https://docs.livekit.io/agents/models/realtime/plugins/gemini/

        Features:
        - Model validation (gemini-2.5-flash, gemini-2.5-flash-native-audio-preview-12-2025)
        - Voice validation (Puck, Charon, Kore, Fenrir, Aoede, Leda, Orus, Zephyr)
        - Mixed realtime mode (text output for separate TTS)
        - System instruction support
        - Vertex AI support
        - Temperature control
        - Thinking mode configuration
        - Affective dialog and proactivity options
        """
        if not google:
            self._logger.error(
                "Google plugin not available. "
                "Install with: pip install 'livekit-plugins-google'"
            )
            raise ImportError("Google plugin not available")

        # Import Modality enum for modalities parameter
        try:
            from google.genai.types import Modality
        except ImportError:
            self._logger.warning("google.genai.types not available, using string modalities")
            Modality = None

        # Get model - default to native audio preview per LiveKit SDK docs
        # Valid Live API models: gemini-2.5-flash-native-audio-preview-12-2025,
        # gemini-2.0-flash-exp (Gemini API), gemini-live-2.5-flash-native-audio (Vertex)
        model = self.config.get("llm_model", "gemini-2.5-flash-native-audio-preview-12-2025")

        # Get and validate voice
        voice = self.config.get("tts_voice", "Puck")
        voice = self._common.validate_gemini_realtime_voice(voice)

        temperature = self.config.get("temperature", 0.8)  # LiveKit default
        instructions = self.config.get("system_prompt", "")

        # Check for mixed realtime mode
        # Auto-enable mixed mode if TTS provider/model is different from LLM realtime model
        tts_provider = self.tts_config.provider.lower()
        tts_model = self.tts_config.model.lower() if self.tts_config.model else ""
        llm_model_lower = model.lower()

        explicit_mixed_mode = self.config.get(
            "mixed_realtime_mode",
            os.getenv("MIXED_REALTIME_MODE", "false").lower() == "true",
        )

        # Determine if TTS is using the same realtime model as LLM
        # Full realtime mode: TTS provider is google/gemini AND TTS model matches LLM model
        # (or TTS model is empty/default, implying use LLM's native audio)
        tts_uses_same_realtime_model = (
            tts_provider in ("google", "gemini")
            and (tts_model == llm_model_lower or tts_model == "" or tts_model == model)
        )

        # Auto-detect mixed mode: if TTS is NOT using the same realtime model
        auto_mixed_mode = not tts_uses_same_realtime_model
        mixed_realtime_mode = explicit_mixed_mode or auto_mixed_mode

        if auto_mixed_mode and not explicit_mixed_mode:
            self._logger.info(
                f"Auto-enabling mixed realtime mode: TTS ({tts_provider}/{tts_model}) "
                f"differs from Gemini realtime LLM ({model})"
            )

        # Check if using Vertex AI
        use_vertex_ai = self.config.get(
            "vertexai",
            os.getenv("USE_VERTEX_AI", "false").lower() == "true",
        )

        # Log mode
        if mixed_realtime_mode:
            self._logger.info(
                "🔀 Mixed Mode: Using Gemini RealtimeModel + separate TTS for audio output"
            )
        else:
            self._logger.info(
                "⚡ Full Realtime Mode: Gemini RealtimeModel (integrated audio)"
            )

        self._logger.info(
            f"Creating Gemini session - model: {model}, voice: {voice}, "
            f"temperature: {temperature}, vertexai: {use_vertex_ai}, mixed_mode: {mixed_realtime_mode}"
        )

        # MIXED MODE: Use standard google.LLM with STT+TTS
        # LiveKit SDK bug: google.realtime.RealtimeModel always sends voice_config
        # even with modalities=[TEXT], causing "Cannot extract voices from non-audio request"
        # Workaround: Use standard pipeline for mixed mode

        # FULL REALTIME MODE: Use google.realtime.RealtimeModel with native audio
        realtime_kwargs: Dict[str, Any] = {
            "model": model,
            "voice": voice,
            "temperature": temperature,
        }

        # Add system instructions if provided
        if instructions:
            # Append language and accent management for Google Realtime models
            combined_instructions = f"{instructions}\n\n{LANGUAGE_ACCENT_PROMPT}"
            realtime_kwargs["instructions"] = combined_instructions
        else:
            # Add language and accent management even without base instructions
            realtime_kwargs["instructions"] = LANGUAGE_ACCENT_PROMPT

        # Vertex AI configuration
        if use_vertex_ai:
            realtime_kwargs["vertexai"] = True
            # Vertex AI uses different model names than Gemini API
            if model == "gemini-2.5-flash-native-audio-preview-12-2025":
                model = "gemini-live-2.5-flash-native-audio"
                realtime_kwargs["model"] = model
            elif model == "gemini-2.0-flash-exp":
                model = "gemini-live-2.5-flash-native-audio"
                realtime_kwargs["model"] = model
            project_id = self.config.get(
                "google_project_id", os.getenv("GOOGLE_CLOUD_PROJECT")
            )
            location = self.config.get(
                "google_location", os.getenv("GOOGLE_CLOUD_LOCATION", "asia-south1")
            )
            if project_id:
                realtime_kwargs["project"] = project_id
            if location:
                realtime_kwargs["location"] = location
            self._logger.info(f"Using Vertex AI: project={project_id}, location={location}")

        # Optional: Thinking mode configuration (for native-audio models)
        thinking_enabled = self.config.get("thinking_enabled", False)
        if thinking_enabled:
            try:
                from google.genai import types as genai_types
                realtime_kwargs["thinking_config"] = genai_types.ThinkingConfig(
                    include_thoughts=self.config.get("include_thoughts", False),
                )
                self._logger.info("Thinking mode enabled")
            except ImportError:
                self._logger.warning("ThinkingConfig not available")

        # Optional: Affective dialog (only for supported models, off by default)
        if self.config.get("enable_affective_dialog", False):
            realtime_kwargs["enable_affective_dialog"] = True
            self._logger.info("Affective dialog enabled")

        # Optional: Proactivity (only for supported models, off by default)
        # Sending proactivity=True to unsupported models causes "invalid argument" rejection
        if self.config.get("proactivity", False):
            realtime_kwargs["proactivity"] = True
            self._logger.info("Proactivity enabled")

        # Create the RealtimeModel
        self._logger.info(f"Gemini RealtimeModel kwargs: {realtime_kwargs}")
        llm_model = google.realtime.RealtimeModel(**realtime_kwargs)
        self._logger.info(f"Created Gemini RealtimeModel: voice={voice}")

        # Build session kwargs
        # In full realtime mode, skip VAD — Gemini handles turn detection natively.
        # In mixed mode, keep VAD for STT-based pipeline.
        session_kwargs: Dict[str, Any] = {
            "userdata": userdata,
            "llm": llm_model,
        }
        if mixed_realtime_mode or vad is not None:
            session_kwargs["vad"] = vad

        # Handle TTS based on mode
        if mixed_realtime_mode:
            # Mixed mode: Create separate TTS for audio output
            try:
                tts = self.create_tts()
                session_kwargs["tts"] = tts
                self._logger.info(
                    f"Mixed realtime mode: TTS ({tts_provider}) handles audio output"
                )
            except Exception as e:
                self._logger.error(f"Failed to create TTS in mixed mode: {e}")
                raise
        else:
            # Full realtime mode: LLM handles audio natively
            # Skip TTS creation to avoid Google Cloud TTS credential errors
            # when TTS provider is google/gemini (same as realtime LLM)
            self._logger.info(
                f"Full Gemini realtime mode: LLM ({model}) handles audio natively. "
                "Skipping separate TTS creation."
            )

        return AgentSession(**session_kwargs)

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _lazy_import_plugin(self, plugin_name: str) -> Optional[Any]:
        """
        Lazily import an optional LiveKit plugin.

        Args:
            plugin_name: Name of the plugin (e.g., 'speechmatics', 'aws')

        Returns:
            Plugin module if available, None otherwise
        """
        if plugin_name in self._plugin_cache:
            return self._plugin_cache[plugin_name]

        try:
            import importlib
            module = importlib.import_module(f"livekit.plugins.{plugin_name}")
            self._plugin_cache[plugin_name] = module
            self._logger.debug(f"Loaded optional plugin: {plugin_name}")
            return module
        except ImportError:
            self._logger.debug(f"Optional plugin not available: {plugin_name}")
            self._plugin_cache[plugin_name] = None
            return None

    def get_service_config(self, service_type: str) -> ServiceConfig:
        """Get configuration for a specific service type."""
        if service_type == "stt":
            return ServiceConfig(
                provider=self.config.get("stt_provider", "deepgram"),
                model=self.config.get("stt_model", "nova-3"),
                language=self.config.get("language", "multi"),
            )
        elif service_type == "llm":
            return ServiceConfig(
                provider=self.config.get("llm_provider", "openai"),
                model=self.config.get("llm_model", "gpt-4o"),
                extra={"temperature": self.config.get("temperature", 0.3)},
            )
        elif service_type == "tts":
            return ServiceConfig(
                provider=self.config.get("tts_provider", DEFAULT_TTS_PROVIDER),
                model=self.config.get("tts_model", DEFAULT_TTS_MODEL),
                voice=self.config.get("tts_voice", DEFAULT_TTS_VOICE),
            )
        else:
            raise ValueError(f"Unknown service type: {service_type}")

    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update factory configuration."""
        self.config.update(updates)
        if "mode" in updates:
            self.mode = updates["mode"]
        if "speaking_plan" in updates:
            self.speaking_plan = updates["speaking_plan"]

    # =========================================================================
    # Backward Compatibility Aliases (used by lazy_factory.py)
    # =========================================================================

    def _create_stt_service(self) -> Any:
        """Alias for _create_plugin_stt() - used by lazy_factory.py."""
        return self.create_stt()

    def _create_llm_service(self) -> Any:
        """Alias for _create_plugin_llm() - used by lazy_factory.py."""
        return self.create_llm()

    def _create_tts_service(self) -> Any:
        """Alias for _create_plugin_tts() - used by lazy_factory.py."""
        return self.create_tts()