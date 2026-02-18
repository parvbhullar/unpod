import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set

# =============================================================================
# Default TTS Configuration (Single Source of Truth)
# =============================================================================
DEFAULT_TTS_PROVIDER = os.getenv("DEFAULT_TTS_PROVIDER", "inworld")
DEFAULT_TTS_MODEL = os.getenv("DEFAULT_TTS_MODEL", "inworld-tts-1.5-max")
DEFAULT_TTS_VOICE = os.getenv("DEFAULT_TTS_VOICE", "Riya")

# =============================================================================
# Unpod to Inworld Model Mapping
# =============================================================================
UNPOD_TO_INWORLD_MODEL_MAP: dict[str, str] = {
    "unpod-tts-1.5-max": "inworld-tts-1.5-max",
    "unpod-tts-1.5": "inworld-tts-1.5-mini",
    "unpod-tts-1.1": "inworld-tts-1-max",
    "unpod-tts-1": "inworld-tts-1",
}


def normalize_tts_provider_model(provider: str, model: str) -> tuple[str, str]:
    normalized_provider = provider.lower()
    normalized_model = model
    model_lower = model.lower()

    if "inworld" in model_lower or "unpod" in model_lower:
        normalized_provider = "inworld"

    if normalized_provider == "unpod":
        normalized_provider = "inworld"

    # Normalize legacy Inworld model naming that used "v" in the version.
    # Example: inworld-tts-v1.5-max -> inworld-tts-1.5-max
    if model_lower.startswith("inworld-tts-v"):
        normalized_model = model.replace("inworld-tts-v", "inworld-tts-", 1)

    if model in UNPOD_TO_INWORLD_MODEL_MAP:
        normalized_model = UNPOD_TO_INWORLD_MODEL_MAP[model]
    elif model.startswith("unpod-"):
        normalized_model = model.replace("unpod-", "inworld-", 1)

    return normalized_provider, normalized_model


# =============================================================================
# Fallback Provider Chains (ordered by priority)
# =============================================================================
STT_FALLBACK_CHAIN: list = [
    {"provider": "deepgram", "model": "nova-3"},
    {"provider": "openai", "model": "whisper-1"},
]

LLM_FALLBACK_CHAIN: list = [
    {"provider": "openai", "model": "gpt-4o-mini"},
    {"provider": "openai", "model": "gpt-4o"},
]

TTS_FALLBACK_CHAIN: list = [
    {
        "provider": DEFAULT_TTS_PROVIDER,
        "model": DEFAULT_TTS_MODEL,
        "voice": DEFAULT_TTS_VOICE,
    },
    {
        "provider": "cartesia",
        "model": "sonic-3",
        "voice": "95d51f79-c397-46f9-b49a-23763d3eaa2d",
    },
]

# =============================================================================
# Inference Model Registries
# =============================================================================
INFERENCE_LLM_MODELS: Dict[str, list] = {
    "openai": [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4.1",
        "gpt-4.1-mini",
        "gpt-4.1-nano",
        "gpt-5",
        "gpt-5-mini",
        "gpt-5-nano",
        "gpt-oss-120b",
    ],
    "moonshotai": ["kimi-k2-instruct"],
    "google": [
        "gemini-3-pro",
        "gemini-3-flash",
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
    ],
}

INFERENCE_STT_MODELS: Dict[str, list] = {
    "assemblyai": ["universal-streaming", "universal-streaming-multilingual"],
    "cartesia": ["ink-whisper"],
    "deepgram": [
        "nova-3", "nova-3-general", "nova-3-medical",
        "nova-2", "nova-2-general", "nova-2-medical",
        "nova-2-conversationalai", "nova-2-phonecall",
        "flux-general",
    ],
    "elevenlabs": ["scribe_v2_realtime"],
}

INFERENCE_TTS_MODELS: Dict[str, list] = {
    "cartesia": ["sonic-3"],
    "unpod": ["sonic-3"],
    "elevenlabs": ["eleven_flash_v2_5", "eleven_multilingual_v2"],
    "rime": ["arcana"],
}

INFERENCE_TTS_DEFAULT_VOICES: Dict[str, str] = {
    "cartesia": "9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
    "elevenlabs": "21m00Tcm4TlvDq8ikWAM",
    "inworld": DEFAULT_TTS_VOICE,
    "rime": "celeste",
    "deepgram": "asteria",
    "gemini": "Kore",
    "google": "Kore",
}

MODELS_WITHOUT_TEMPERATURE_SUPPORT: Dict[str, list] = {
    "openai": ["gpt-5", "gpt-5-mini", "gpt-5-nano"],
}

DEEPGRAM_TTS_VOICES: list = [
    "asteria",
    "athena",
    "apollo",
    "arcas",
    "hera",
    "helios",
    "luna",
    "orion",
    "orpheus",
    "perseus",
    "stella",
    "zeus",
    "thalia",
    "andromeda",
    "odysseus",
    "theia",
]

INFERENCE_ELEVENLABS_VOICES: list = [
    "21m00Tcm4TlvDq8ikWAM",
    "AZnzlk1XvdvUeBnXmlld",
    "EXAVITQu4vr4xnSDxMaL",
    "ErXwobaYiN019PkySvjV",
    "MF3mGyEYCl7XYWbV9V6O",
    "TxGEqnHWrfWFTfGW9XjX",
    "VR6AewLTigWG4xSOukaG",
    "pNInz6obpgDQGcFmaJgB",
    "yoZ06aMxZJJ28mfd3POQ",
    "jsCqWAovK2LkecY7zXl4",
    "oWAxZDx7w5VEj9dCyTzz",
    "pqHfZKP75CvOlQylNhV4",
    "N2lVS1w4EtoT3dr4eOWO",
    "IKne3meq5aSn9XLyUdCD",
    "XB0fDUnXU5powFXDhCwa",
    "Xb7hH8MSUJpSbSDYk0k2",
    "onwK4e9ZLuTAKqWW03F9",
    "CwhRBWXzGAHq8TQ4Fs17",
    "JBFqnCBsd6RMkjVDRZzb",
    "TX3LPaxmHKxFdv7VOQHJ",
]

# =============================================================================
# Realtime Voice/Model Constants
# =============================================================================

# Valid OpenAI Realtime voices
# Reference: https://platform.openai.com/docs/guides/realtime-conversations#voice-options
OPENAI_REALTIME_VOICES: list[str] = [
    "alloy", "ash", "ballad", "coral", "echo", "marin", "sage", "shimmer", "verse"
]

# Valid OpenAI Realtime models
# Reference: https://docs.livekit.io/agents/models/realtime/plugins/openai/
OPENAI_REALTIME_MODELS: list[str] = [
    "gpt-realtime",  # Default model
    "gpt-4o-realtime-preview",
    "gpt-4o-realtime-preview-2024-12-17",
]

# Valid Gemini Realtime voices
# Reference: https://ai.google.dev/gemini-api/docs/live#change-voices
# Reference: https://firebase.google.com/docs/ai-logic/live-api/configuration
GEMINI_REALTIME_VOICES: list[str] = [
    "Aoede",  # Breezy
    "Puck",  # Default, Upbeat
    "Charon",  # Deep
    "Kore",  # Firm
    "Fenrir",  # Excitable
    "Leda",  # Youthful
    "Orus",  # Firm
    "Zephyr",  # Bright
    "Achernar",  # Bright
]

# Valid Gemini TTS models
# Reference: https://docs.livekit.io/agents/models/tts/plugins/gemini/
GEMINI_TTS_MODELS: list[str] = [
    "gemini-2.5-flash-preview-tts",
    "chirp-3.0-generate-001",
]

# Valid Gemini Realtime models
# Reference: https://docs.livekit.io/agents/models/realtime/plugins/gemini/
# Reference: https://docs.pipecat.ai/server/services/s2s/gemini-live-vertex
GEMINI_REALTIME_MODELS: list[str] = [
    # "gemini-2.5-flash-native-audio-latest",  # Default - recommended
    "gemini-2.0-flash-live-001",  # Stable Live API model
    "gemini-2.0-flash-exp",  # Experimental
    "gemini-2.5-flash-native-audio-preview-12-2025",  # Native audio preview
    "gemini-2.5-flash-native-audio-preview-09-2025",  # Native audio preview (older)
]

# Unified LLM Realtime Models (combines OpenAI + Gemini)
# Used for auto-detecting realtime mode from model name
LLM_REALTIME_MODELS: list[str] = [
    # OpenAI Realtime
    "gpt-realtime",
    "gpt-realtime-mini",
    "gpt-4o-realtime-preview",
    "gpt-4o-realtime-preview-2024-12-17",
    # Gemini Realtime / Live
    "gemini-2.5-flash-native-audio-latest",
    "gemini-2.5-flash-native-audio-preview-12-2025",
    "gemini-2.5-flash-native-audio-preview-09-2025",
]


def is_realtime_model(model: str) -> bool:
    """
    Check if the given model is a realtime/live model.

    Args:
        model: Model name to check

    Returns:
        True if model is a realtime model, False otherwise
    """
    if not model:
        return False
    model_lower = model.lower()

    # Check for exact match first
    for rm in LLM_REALTIME_MODELS:
        if rm.lower() == model_lower:
            return True

    # Check if model contains realtime/live/native-audio keywords
    # This handles variations like provider prefixes (openai/gpt-realtime)
    realtime_keywords = ["realtime", "-live-", "live-", "native-audio"]
    if any(kw in model_lower for kw in realtime_keywords):
        return True

    return False


# =============================================================================
# Google Model Validation via ListModels API
# =============================================================================
_google_models_cache: Set[str] = set()
_google_models_cache_time: float = 0.0
_GOOGLE_MODELS_CACHE_TTL: float = 3600.0  # 1 hour

_google_models_logger = logging.getLogger("service_common.google_models")


def fetch_google_available_models() -> Set[str]:
    """Fetch available models from Google Gemini API with TTL caching."""
    global _google_models_cache, _google_models_cache_time

    if _google_models_cache and (time.monotonic() - _google_models_cache_time) < _GOOGLE_MODELS_CACHE_TTL:
        return _google_models_cache

    try:
        from google import genai

        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            _google_models_logger.warning(
                "GOOGLE_API_KEY/GEMINI_API_KEY not set, "
                "skipping model validation"
            )
            return set()

        client = genai.Client(api_key=api_key)
        models: Set[str] = set()
        for model in client.models.list():
            name = model.name or ""
            # API returns "models/gemini-2.5-flash", strip prefix
            short = name.removeprefix("models/")
            models.add(short)
            models.add(name)

        _google_models_cache = models
        _google_models_cache_time = time.monotonic()
        _google_models_logger.info(
            f"Fetched {len(models) // 2} Google models"
        )
        return models

    except Exception as e:
        _google_models_logger.warning(
            f"Failed to fetch Google models list: {e}"
        )
        return _google_models_cache


def validate_google_model(
    model: str,
    default: str = "gemini-3-flash",
    logger: Optional[logging.Logger] = None,
) -> str:
    """Validate a Google model name against the ListModels API.

    Returns the model if valid, or the default with a warning if not.
    """
    if not model:
        return default

    available = fetch_google_available_models()
    if not available:
        # API unreachable — let Google reject it downstream
        return model

    if model in available:
        return model

    log = logger or _google_models_logger
    log.warning(
        f"Google model '{model}' not found via ListModels API. "
        f"Defaulting to '{default}'."
    )
    return default


# Languages not supported by AssemblyAI streaming models
# These languages will use auto-detection via the multilingual model
ASSEMBLYAI_UNSUPPORTED_LANGUAGES: list[str] = [
    "hi", "ta", "kn", "te", "ml", "pa", "mr", "bn", "gu",
]

# Language code mapping for Gemini
GEMINI_LANGUAGE_MAP: Dict[str, str] = {
    "en": "en-US",
    "en-us": "en-US",
    "en-in": "en-IN",
    "hi": "hi-IN",
    "pa": "pa-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "kn": "kn-IN",
    "ml": "ml-IN",
    "mr": "mr-IN",
    "bn": "bn-IN",
    "gu": "gu-IN",
}

# =============================================================================
# Model Context Limits (tokens)
# =============================================================================
MODEL_CONTEXT_LIMITS: Dict[str, int] = {
    # Cerebras models
    "llama3.1-8b": 8192,
    "llama-3.1-8b": 8192,
    "llama-3.1-8b-instant": 8192,
    "llama3.3-70b": 128000,
    "llama-3.3-70b": 128000,
    # Groq models
    "llama-3.1-70b-versatile": 131072,
    "llama-3.2-90b-vision-preview": 8192,
    "mixtral-8x7b-32768": 32768,
    # OpenAI models
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4-turbo": 128000,
    "gpt-4": 8192,
    "gpt-3.5-turbo": 16385,
    # Google models
    "gemini-3-pro": 1000000,
    "gemini-3-flash": 1000000,
    "gemini-2.5-pro": 1000000,
    "gemini-2.5-flash": 1000000,
    "gemini-2.5-flash-lite": 1000000,
    "gemini-2.0-flash": 1000000,
    "gemini-2.0-flash-lite": 1000000,
    "gemini-1.5-pro": 1000000,
    "gemini-1.5-flash": 1000000,
    # Anthropic models
    "claude-3-opus": 200000,
    "claude-3-sonnet": 200000,
    "claude-3-haiku": 200000,
    "claude-3-5-sonnet": 200000,
    "claude-3-5-haiku": 200000,
    # Default fallback
    "_default": 8192,
}


def get_model_context_limit(model: str) -> int:
    """Get context limit for a model, with fuzzy matching."""
    model_lower = model.lower()
    # Exact match
    if model_lower in MODEL_CONTEXT_LIMITS:
        return MODEL_CONTEXT_LIMITS[model_lower]
    # Partial match (e.g., "llama3.1-8b" in "cerebras/llama3.1-8b")
    for key, limit in MODEL_CONTEXT_LIMITS.items():
        if key in model_lower or model_lower in key:
            return limit
    return MODEL_CONTEXT_LIMITS["_default"]


def estimate_tokens(text: str) -> int:
    """Estimate token count from text (approx 4 chars per token for English)."""
    if not text:
        return 0
    return len(text) // 4 + 1

# =============================================================================
# Unified Provider API Keys
# =============================================================================
PROVIDER_API_KEYS: Dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "deepgram": "DEEPGRAM_API_KEY",
    "google": "GOOGLE_CREDENTIALS",
    "groq": "GROQ_API_KEY",
    "azure": "AZURE_SPEECH_API_KEY",
    "aws": "AWS_ACCESS_KEY_ID",
    "cartesia": "CARTESIA_API_KEY",
    "assemblyai": "ASSEMBLYAI_API_KEY",
    "gladia": "GLADIA_API_KEY",
    "lmnt": "LMNT_API_KEY",
    "elevenlabs": "ELEVEN_API_KEY",
    "sarvam": "SARVAM_API_KEY",
    "playht": "PLAYHT_API_KEY",
    "soniox": "SONIOX_API_KEY",
    "fal": "FAL_API_KEY",
    "speechmatics": "SPEECHMATICS_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "cerebras": "CEREBRAS_API_KEY",
    "xai": "XAI_API_KEY",
}


@dataclass(frozen=True)
class STTConfig:
    provider: str
    model: str
    language: str = "en"
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider", self.provider.lower())
        # Ensure extra is never None to prevent iteration errors
        if self.extra is None:
            object.__setattr__(self, "extra", {})

    @property
    def smart_format(self) -> bool:
        return self.extra.get("smart_format", True)

    @property
    def endpointing_ms(self) -> int:
        return self.extra.get("endpointing_ms", 25)

    @property
    def use_finals_only(self) -> bool:
        return self.extra.get("use_finals_only", False)

    @property
    def filler_words(self) -> bool:
        return self.extra.get("filler_words", False)

    @property
    def profanity_filter(self) -> bool:
        return self.extra.get("profanity_filter", False)

    @property
    def min_volume(self) -> Optional[float]:
        return self.extra.get("min_volume")

    @property
    def max_silence_duration_secs(self) -> Optional[float]:
        return self.extra.get("max_silence_duration_secs")

    @property
    def format_turns(self) -> Optional[bool]:
        return self.extra.get("format_turns")

    @property
    def end_of_turn_confidence_threshold(self) -> Optional[float]:
        return self.extra.get("end_of_turn_confidence_threshold")

    @property
    def min_end_of_turn_silence_when_confident(self) -> Optional[float]:
        return self.extra.get("min_end_of_turn_silence_when_confident")

    @property
    def max_turn_silence(self) -> Optional[float]:
        return self.extra.get("max_turn_silence")

    @property
    def keyterms_prompt(self) -> Optional[str]:
        return self.extra.get("keyterms_prompt")

    @property
    def keyterms(self) -> list[str]:
        value = self.extra.get("keyterms", [])
        return value if value is not None else []


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    model: str
    temperature: float = 0.4
    max_tokens: int = 500
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        provider_map = {"gemini": "google"}
        normalized = provider_map.get(self.provider.lower(), self.provider.lower())
        object.__setattr__(self, "provider", normalized)
        # Ensure extra is never None to prevent iteration errors
        if self.extra is None:
            object.__setattr__(self, "extra", {})

    @property
    def reasoning_effort(self) -> Optional[str]:
        return self.extra.get("reasoning_effort")

    @property
    def parallel_tool_calls(self) -> bool:
        return self.extra.get("parallel_tool_calls", True)

    @property
    def top_p(self) -> Optional[float]:
        return self.extra.get("top_p")

    @property
    def prompt_cache_key(self) -> Optional[str]:
        return self.extra.get("prompt_cache_key")

    @property
    def context_limit(self) -> int:
        """Get the context token limit for this model."""
        return get_model_context_limit(self.model)


@dataclass(frozen=True)
class TTSConfig:
    provider: str
    model: str
    voice: str
    language: str = "en"
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        provider, model = normalize_tts_provider_model(self.provider, self.model)
        object.__setattr__(self, "provider", provider)
        object.__setattr__(self, "model", model)
        # Ensure extra is never None to prevent iteration errors
        if self.extra is None:
            object.__setattr__(self, "extra", {})

    @property
    def speed(self) -> float:
        return self.extra.get("voice_speed", self.extra.get("speed", 1.0))

    @property
    def voice_instructions(self) -> Optional[str]:
        return self.extra.get("voice_instructions")

    @property
    def emotion(self) -> Optional[str]:
        return self.extra.get("emotion")

    @property
    def volume(self) -> float:
        return self.extra.get("volume", 1.0)

    @property
    def stability(self) -> Optional[float]:
        return self.extra.get("stability")

    @property
    def similarity_boost(self) -> Optional[float]:
        return self.extra.get("similarity_boost")

    @property
    def style(self) -> Optional[float]:
        return self.extra.get("style")

    @property
    def use_speaker_boost(self) -> Optional[bool]:
        return self.extra.get("use_speaker_boost")

    @property
    def streaming_latency(self) -> int:
        return self.extra.get("streaming_latency", 3)

    @property
    def temperature(self) -> Optional[float]:
        return self.extra.get("voice_temperature", None)

    @property
    def top_p(self) -> Optional[float]:
        return self.extra.get("top_p")

    @property
    def pitch(self) -> float:
        return self.extra.get("pitch", 0.3)

    @property
    def pace(self) -> float:
        return self.extra.get("pace", self.speed)

    @property
    def loudness(self) -> float:
        return self.extra.get("loudness", 1)

    @property
    def speech_engine(self) -> str:
        return self.extra.get("speech_engine", "generative")

    @property
    def gender(self) -> str:
        return self.extra.get("gender", "neutral")

    @property
    def sample_rate(self) -> int:
        return self.extra.get("sample_rate", 24000)


class ServiceCommon:
    def __init__(
        self,
        config: Dict[str, Any],
        logger: Optional[logging.Logger] = None,
        room_name: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.room_name = room_name
        self.session_id = session_id

        self.stt_config = self.parse_stt_config()
        self.llm_config = self.parse_llm_config()
        self.tts_config = self.parse_tts_config()

    def parse_stt_config(self) -> STTConfig:
        return STTConfig(
            provider=self.config.get("stt_provider", "deepgram"),
            model=self.config.get("stt_model", "nova-3"),
            language=self.config.get("language", "en"),
            extra={
                "smart_format": self.config.get("stt_smart_format", True),
                "filler_words": self.config.get("stt_filler_words", False),
                "endpointing_ms": self.config.get("stt_endpointing_ms", 20),  # Reduced from 25ms for faster endpointing
                "profanity_filter": self.config.get("stt_profanity_filter", False),
                "use_finals_only": self.config.get(
                    "use_final_transcriptions_only", False
                ),
                # Deepgram inference extra_kwargs for faster EOU detection
                "interim_results": self.config.get("stt_interim_results", True),
                "no_delay": self.config.get("stt_no_delay", True),
                "utterance_end_ms": self.config.get("stt_utterance_end_ms", 80),  # Max silence before ending utterance
                "min_volume": self.config.get("stt_min_volume"),
                "max_silence_duration_secs": self.config.get(
                    "stt_max_silence_duration_secs"
                ),
                "format_turns": self.config.get("stt_format_turns"),
                "end_of_turn_confidence_threshold": self.config.get(
                    "stt_end_of_turn_confidence_threshold"
                ),
                "min_end_of_turn_silence_when_confident": self.config.get(
                    "stt_min_end_of_turn_silence_when_confident"
                ),
                "max_turn_silence": self.config.get("stt_max_turn_silence"),
                "keyterms_prompt": self.config.get("stt_keyterms_prompt"),
                "keyterms": self.config.get("stt_keyterms", []),
            },
        )

    def parse_llm_config(self) -> LLMConfig:
        return LLMConfig(
            provider=self.config.get("llm_provider", "openai"),
            model=self.config.get("llm_model", "gpt-4o-mini"),
            temperature=self.config.get("temperature", 0.4),
            max_tokens=self.config.get("max_tokens", 500),
            extra={
                "reasoning_effort": self.config.get("reasoning_effort"),
                "parallel_tool_calls": self.config.get("parallel_tool_calls", True),
                "top_p": self.config.get("llm_top_p", 0.9),
                "prompt_cache_key": self.config.get("prompt_cache_key"),
            },
        )

    def parse_tts_config(self) -> TTSConfig:
        return TTSConfig(
            provider=self.config.get("tts_provider", DEFAULT_TTS_PROVIDER),
            model=self.config.get("tts_model", DEFAULT_TTS_MODEL),
            voice=self.config.get("tts_voice", DEFAULT_TTS_VOICE),
            language=self.config.get("language", "en"),
            extra={
                "voice_speed": self.config.get(
                    "voice_speed", self.config.get("speed", 1.0)
                ),
                "voice_instructions": self.config.get("voice_instructions"),
                "voice_inference": self.config.get("voice_inference", False),
                "emotion": self.config.get("tts_emotion"),
                "volume": self.config.get("tts_volume", 1.0),
                "stability": self.config.get("tts_stability"),
                "similarity_boost": self.config.get("tts_similarity_boost"),
                "style": self.config.get("tts_style"),
                "use_speaker_boost": self.config.get("tts_use_speaker_boost"),
                "streaming_latency": self.config.get("tts_streaming_latency", 3),
                "inactivity_timeout": self.config.get("tts_inactivity_timeout"),
                "apply_text_normalization": self.config.get(
                    "tts_apply_text_normalization"
                ),
                "voice_temperature": self.config.get("voice_temperature"),
                "top_p": self.config.get("tts_top_p"),
                "inworld_max_connections": self.config.get(
                    "tts_inworld_max_connections", 20
                ),
                "inworld_idle_timeout": self.config.get(
                    "tts_inworld_idle_timeout", 300.0
                ),
                "inworld_connect_timeout": self.config.get(
                    "tts_inworld_connect_timeout", 30.0
                ),
                "inworld_total_timeout": self.config.get(
                    "tts_inworld_total_timeout", 60.0
                ),
                "pitch": self.config.get("tts_pitch", self.config.get("pitch")),
                "pace": self.config.get("tts_pace", self.config.get("pace")),
                "loudness": self.config.get(
                    "tts_loudness", self.config.get("loudness", 1)
                ),
                "speech_engine": self.config.get("tts_speech_engine", "generative"),
                "gender": self.config.get("tts_gender", self.config.get("gender", "neutral")),
                "sample_rate": self.config.get("tts_sample_rate", 24000),
            },
        )

    def validate_provider(self, provider: str) -> tuple[bool, str]:
        provider_key = provider.lower()
        # Azure uses different keys depending on service (LLM vs Speech)
        if provider_key == "azure":
            if os.getenv("AZURE_IN_API_KEY") or os.getenv("AZURE_SPEECH_API_KEY"):
                return True, ""
            return False, "AZURE_IN_API_KEY or AZURE_SPEECH_API_KEY not set for azure"

        env_var = PROVIDER_API_KEYS.get(provider_key)
        if env_var and not os.getenv(env_var):
            return False, f"{env_var} not set for {provider}"
        return True, ""

    def has_api_key(self, provider: str) -> bool:
        is_valid, _ = self.validate_provider(provider)
        return is_valid

    def get_voice_optimized_max_tokens(self, max_tokens: Optional[int] = None) -> int:
        value = max_tokens if max_tokens is not None else self.llm_config.max_tokens
        if value < 300:
            self.logger.warning(
                f"max_tokens={value} is low for voice (<300). "
                "Responses may be cut off mid-sentence. Consider 500-800."
            )
        elif value > 1000:
            self.logger.warning(
                f"max_tokens={value} is high for voice (>1000). "
                "Responses may feel too long. Consider 500-800."
            )
        return value

    def get_voice_optimized_temperature(
        self, temperature: Optional[float] = None
    ) -> float:
        value = temperature if temperature is not None else self.llm_config.temperature
        if value > 0.6:
            self.logger.warning(
                f"temperature={value} is high for voice (>0.6). "
                "Agent may ramble. Consider 0.3-0.5."
            )
        return value

    def build_cache_key(
        self,
        room_name: Optional[str] = None,
        session_id: Optional[str] = None,
        user_state: Optional[Any] = None,
    ) -> str:
        room = (
            room_name
            or self.room_name
            or self.config.get("room_name", "default_room")
        )
        session = (
            session_id
            or self.session_id
            or getattr(user_state, "session_id", None)
            or self.config.get("session_id", "default")
        )
        cache_key = f"{room}:{session}"
        self.logger.debug(f"LLM cache key generated: {cache_key}")
        return cache_key

    def model_supports_inference(self, service_type: str) -> bool:
        if service_type == "stt":
            cfg = self.stt_config
            registry = INFERENCE_STT_MODELS
        elif service_type == "llm":
            cfg = self.llm_config
            registry = INFERENCE_LLM_MODELS
        elif service_type == "tts":
            cfg = self.tts_config
            registry = INFERENCE_TTS_MODELS
        else:
            return False

        if cfg.provider not in registry:
            return False
        return cfg.model in registry[cfg.provider]

    def is_voice_inference_compatible(self, provider: str, voice: str) -> bool:
        if provider == "elevenlabs":
            if voice in INFERENCE_ELEVENLABS_VOICES:
                return True
            self.logger.debug(
                f"ElevenLabs voice '{voice}' not inference-compatible."
            )
            return False
        if provider == "cartesia":
            return True
        if provider == "deepgram":
            return voice.lower() in DEEPGRAM_TTS_VOICES
        if provider in ("rime", "inworld"):
            return True
        return True

    def get_inference_flag(self, config_key: str) -> bool:
        inference_value = self.config.get(config_key, False)
        if isinstance(inference_value, str):
            return inference_value.strip() == "[v]"
        return bool(inference_value)

    def should_use_inference(self, service_type: str) -> bool:
        env_mode = os.getenv("AGENT_INFRA_MODE", "").lower()
        inference_mode = env_mode == "inference" and (
            self.model_supports_inference(service_type)
            or self.get_inference_flag(f"{service_type}_inference")
        )

        if inference_mode and service_type == "tts":
            cfg = self.tts_config
            if not self.is_voice_inference_compatible(cfg.provider, cfg.voice):
                if self.config.get("voice_inference", False):
                    self.logger.info(
                        f"TTS voice '{cfg.voice}' is instance compatible {cfg.provider}."
                    )
                    return True
                self.logger.info(
                    f"TTS voice '{cfg.voice}' not inference-compatible for {cfg.provider}. "
                    "Using plugin mode instead."
                )
                return False
        return inference_mode

    def model_supports_temperature(self, provider: str, model: str) -> bool:
        unsupported_models = MODELS_WITHOUT_TEMPERATURE_SUPPORT.get(provider, [])
        return model not in unsupported_models

    def should_fallback_tts(self, provider: str, model: str) -> bool:
        if provider == "unpod":
            return True

        if self.get_inference_flag("tts_inference"):
            self.logger.info(
                "TTS inference flag is True in database. "
                f"Using {provider}/{model} despite not being in registry."
            )
            return False

        if provider not in INFERENCE_TTS_MODELS:
            return True

        valid_models = INFERENCE_TTS_MODELS.get(provider, [])
        return model not in valid_models

    def looks_like_uuid(self, value: str) -> bool:
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            re.IGNORECASE,
        )
        return bool(uuid_pattern.match(value))

    def validate_tts_voice(self, provider: str, voice: str) -> str:
        if provider == "deepgram":
            return self.validate_deepgram_voice(voice)
        if provider == "rime":
            return voice.lower()
        if provider == "cartesia":
            if not self.looks_like_uuid(voice):
                self.logger.warning(
                    f"Voice '{voice}' doesn't look like a Cartesia voice ID. "
                    f"Using default: {INFERENCE_TTS_DEFAULT_VOICES['cartesia']}"
                )
                return INFERENCE_TTS_DEFAULT_VOICES["cartesia"]
            return voice
        if provider == "elevenlabs":
            return voice
        if provider == "inworld":
            return voice
        if provider in INFERENCE_TTS_DEFAULT_VOICES:
            return INFERENCE_TTS_DEFAULT_VOICES[provider]
        return voice

    def validate_deepgram_voice(self, voice: str) -> str:
        voice_lower = voice.lower()
        if voice_lower in DEEPGRAM_TTS_VOICES:
            return voice_lower
        if self.looks_like_uuid(voice):
            self.logger.warning(
                f"Voice '{voice}' looks like a UUID but Deepgram TTS requires voice names. "
                f"Using default: {INFERENCE_TTS_DEFAULT_VOICES['deepgram']}"
            )
            return INFERENCE_TTS_DEFAULT_VOICES["deepgram"]
        self.logger.warning(
            f"Voice '{voice}' is not a known Deepgram voice. "
            f"Using default: {INFERENCE_TTS_DEFAULT_VOICES['deepgram']}"
        )
        return INFERENCE_TTS_DEFAULT_VOICES["deepgram"]

    def validate_openai_voice(
        self, voice: Optional[str], default: str = "alloy", log_warning: bool = True
    ) -> str:
        valid_openai_voices = [
            "alloy",
            "ash",
            "ballad",
            "coral",
            "echo",
            "fable",
            "onyx",
            "nova",
            "sage",
            "shimmer",
            "verse",
        ]

        if voice and voice in valid_openai_voices:
            return voice

        if log_warning and voice:
            self.logger.warning(
                f"Invalid OpenAI TTS voice '{voice}'. "
                f"Valid voices: {', '.join(valid_openai_voices)}. "
                f"Defaulting to '{default}'."
            )
        return default

    def get_inference_credentials(self, _type= "llm") -> tuple[str, str, str]:
        """
        Get LiveKit inference gateway credentials for any supported provider.

        Returns:
            Tuple of (base_url, api_key, model_ref) for inference mode.
            model_ref is formatted as "provider/model" (e.g., "google/gemini-2.5-pro")
        """
        from livekit.agents.inference._utils import create_access_token

        base_url = os.getenv(
            "LIVEKIT_INFERENCE_URL", "https://agent-gateway.livekit.cloud/v1"
        )
        lk_api_key = os.getenv(
            "LIVEKIT_INFERENCE_API_KEY", os.getenv("LIVEKIT_API_KEY", "")
        )
        lk_api_secret = os.getenv(
            "LIVEKIT_INFERENCE_API_SECRET", os.getenv("LIVEKIT_API_SECRET", "")
        )

        # Log which env vars are being used (names only, no secrets)
        key_source = (
            "LIVEKIT_INFERENCE_API_KEY"
            if os.getenv("LIVEKIT_INFERENCE_API_KEY")
            else "LIVEKIT_API_KEY"
        )
        secret_source = (
            "LIVEKIT_INFERENCE_API_SECRET"
            if os.getenv("LIVEKIT_INFERENCE_API_SECRET")
            else "LIVEKIT_API_SECRET"
        )
        self.logger.info(
            "Inference credentials source: key=%s secret=%s base_url=%s",
            key_source,
            secret_source,
            base_url,
        )
        if not lk_api_key or not lk_api_secret:
            self.logger.warning(
                "Inference credentials missing/empty: key_present=%s secret_present=%s",
                bool(lk_api_key),
                bool(lk_api_secret),
            )
        api_key = create_access_token(lk_api_key, lk_api_secret)

        if _type == "stt":
            model_ref = f"{self.stt_config.provider}/{self.stt_config.model}"
        elif _type == "tts":
            model_ref = f"{self.tts_config.provider}/{self.tts_config.model}"
        else:
            model_ref = f"{self.llm_config.provider}/{self.llm_config.model}"

        return base_url, api_key, model_ref

    def validate_openai_tts_model(
        self, model: Optional[str], default: str = "tts-1"
    ) -> str:
        valid_openai_tts_models = [
            "tts-1",
            "tts-1-hd",
            "gpt-4o-mini-tts",
            "gpt-4o-audio-preview",
        ]

        if model and model in valid_openai_tts_models:
            return model

        if model:
            self.logger.warning(
                f"Invalid OpenAI TTS model '{model}'. "
                f"Valid models: {', '.join(valid_openai_tts_models)}. "
                f"Defaulting to '{default}'."
            )

        return default

    def validate_openai_realtime_voice(
        self, voice: Optional[str], default: str = "alloy"
    ) -> str:
        """Validate OpenAI Realtime voice."""
        if voice and (voice in OPENAI_REALTIME_VOICES or self.config.get("voice_realtime")):
            return voice

        if voice:
            self.logger.warning(
                f"Invalid OpenAI Realtime voice '{voice}'. "
                f"Valid voices: {', '.join(OPENAI_REALTIME_VOICES)}. "
                f"Defaulting to '{default}'."
            )
        return default

    def validate_openai_realtime_model(
        self, model: Optional[str], default: str = "gpt-realtime"
    ) -> str:
        """Validate OpenAI Realtime model."""
        if model and (model in OPENAI_REALTIME_MODELS or self.config.get("llm_realtime")):
            return model

        if model:
            self.logger.warning(
                f"Invalid OpenAI Realtime model '{model}'. "
                f"Valid models: {', '.join(OPENAI_REALTIME_MODELS)}. "
                f"Defaulting to '{default}'."
            )
        return default

    def validate_gemini_realtime_voice(
        self, voice: Optional[str], default: str = "Puck"
    ) -> str:
        """Validate Gemini Realtime voice."""
        if voice and (voice in GEMINI_REALTIME_VOICES or self.config.get("voice_realtime")):
            return voice

        if voice:
            self.logger.warning(
                f"Invalid Gemini Realtime voice '{voice}'. "
                f"Valid voices: {', '.join(GEMINI_REALTIME_VOICES)}. "
                f"Defaulting to '{default}'."
            )
        return default

    def validate_gemini_realtime_model(
        self, model: Optional[str], default: str = "gemini-2.5-flash"
    ) -> str:
        """Validate Gemini Realtime model."""
        if model and (model in GEMINI_REALTIME_MODELS or self.config.get("llm_realtime")):
            return model

        if model:
            self.logger.warning(
                f"Invalid Gemini Realtime model '{model}'. "
                f"Valid models: {', '.join(GEMINI_REALTIME_MODELS)}. "
                f"Defaulting to '{default}'."
            )
        return default

    def get_gemini_language_code(self, language: str) -> str:
        """Get Gemini-compatible language code."""
        return GEMINI_LANGUAGE_MAP.get(language.lower(), "en-US")
