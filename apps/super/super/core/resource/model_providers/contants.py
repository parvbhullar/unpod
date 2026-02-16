import enum
from typing import List

from super.core.plugin.base import PluginLocation, PluginStorageFormat
from super.core.resource.model_providers.schema import (
    ModelProviderDetail,
    ModelProviderName,
    ModelProviderService,
    LanguageModelProviderModelInfo,
    EmbeddingModelProviderModelInfo,
)

MODEL_PROVIDERS_DICT = {
    ModelProviderName.OPENAI: ModelProviderDetail(
        name=ModelProviderName.OPENAI,
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="super.core.resource.model_providers.OpenAIProvider",
        ),
    ),
    ModelProviderName.ANTHROPIC: ModelProviderDetail(
        name=ModelProviderName.HUGGINGFACE,
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="super.core.resource.model_providers.AnthropicApiProvider",
        ),
    ),
    ModelProviderName.OLLAMA: ModelProviderDetail(
        name=ModelProviderName.OLLAMA,
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="super.core.resource.model_providers.OllamaApiProvider",
        ),
    ),
    ModelProviderName.DEEPINFRA: ModelProviderDetail(
        name=ModelProviderName.DEEPINFRA,
        location=PluginLocation(
            storage_format=PluginStorageFormat.INSTALLED_PACKAGE,
            storage_route="super.core.resource.model_providers.DeepInfraProvider",
        ),
    ),
}


class AIModelName(str, enum.Enum):
    # OpenAI Models
    OPENAI_ADA = "text-embedding-ada-002"
    OPENAI_GPT3 = "gpt-3.5-turbo-0613"
    OPENAI_GPT3_16K = "gpt-3.5-turbo-16k-0613"
    OPENAI_GPT4 = "gpt-4-0613"
    OPENAI_GPT4_32K = "gpt-4-32k-0314"
    OPENAI_GPT4_TURBO = "gpt-4-1106-preview"
    OPENAI_GPT4_VISION = "gpt-4-vision-preview"
    OPENAI_GPT4_32K_NEW = "gpt-4-32k-0613"
    OPENAI_GPT3_FINETUNE = "ft:gpt-3.5-turbo-0613:recalll::8PE7I1IF"
    OPENAI_GPT4_O = "gpt-4o"
    OPENAI_GPT4_O_MINI = "gpt-4o-mini"
    OPENAI_O3_MINI = "o3-mini"
    OPENAI_REALTIME = "gpt-4o-realtime"
    OPENAI_GPT4O_TRANSCRIBE = "gpt-4o-transcribe"
    OPENAI_WHISPER_1 = "whisper-1"
    OPENAI_TTS_1 = "tts-1"
    OPENAI_TTS_1_HD = "tts-1-hd"
    OPENAI_GPT_5o = 'openai_gpt-5'
    OPENAI_GPT_5o_mini = 'openai_gpt-5-mini'

    # Anthropic Models
    ANTHROPIC_CLAUDE3_HAIKU = "claude-3-haiku-20240307"
    ANTHROPIC_CLAUDE3_SONNET = "claude-3-sonnet-20240229"
    ANTHROPIC_CLAUDE3_OPUS = "claude-3-opus-20240229"
    ANTHROPIC_CLAUDE_SONNET_4 = "claude-sonnet-4-20250514"
    ANTHROPIC_CLAUDE2 = "claude-2"
    ANTHROPIC_CLAUDE2_1 = "claude-2.1"
    ANTHROPIC_CLAUDE2_FULL = "claude-2.0"
    ANTHROPIC_CLAUDE2_INSTANT = "claude-instant-1"
    ANTHROPIC_CLAUDE2_INSTANT_FULL = "claude-instant-1.2"

    # Deepgram Models - STT
    DEEPGRAM_NOVA_2_GENERAL = "nova-2-general"
    DEEPGRAM_NOVA_3_GENERAL = "nova-3-general"
    DEEPGRAM_NOVA_3 = "nova-3"
    NOVA_3_DEEPGRAM='deepgram_nova-3'


    # Deepgram Models - TTS
    DEEPGRAM_AURA_HELIOS_EN = "aura-helios-en"
    DEEPGRAM_AURA_LUNA_EN = "aura-luna-en"
    DEEPGRAM_AURA_ATHENA_EN = "aura-athena-en"
    DEEPGRAM_AURA_ASTERIA_EN = "aura-asteria-en"
    DEEPGRAM_AURA_ARCANIS_EN = "aura-arcanis-en"

    # ElevenLabs Models
    ELEVENLABS_ELEVEN_FLASH_V2_5 = "eleven_flash_v2_5"
    ELEVENLABS_ELEVEN_MULTILINGUAL_V2 = "eleven_multilingual_v2"

    # Cartesia Models
    CARTESIA_SONIC = "sonic"
    CARTESIA_SONIC_2 = "sonic-2"
    CARTESIA_SONIC_TURBO = "sonic-turbo"
    SONIC_2_CARTESIA='cartesia_sonic-2'

    # Google Models
    GOOGLE_CHIRP = "chirp"
    GOOGLE_CHIRP_2 = "chirp_2"
    GOOGLE_TELEPHONY = "telephony"
    GOOGLE_LATEST_LONG = "latest_long"
    GOOGLE_LATEST_SHORT = "latest_short"
    GEMINI_FLASH_2_Lite='Google_google/gemini-2.5-flash-lite'

    # Gemini Models
    GEMINI_REALTIME = "gemini-realtime"
    GEMINI_FLASH = "gemini-2.0-flash-exp"
    GEMINI_FLASH_2 = "gemini-2.0-flash"

    # Sarvam Models
    SARVAM_STT = "sarvam_saarika:v2.5"
    SARVAM_TTS = "sarvam_bulbul:v2"

    # Soniox Models
    SONIOX_STT = "stt-rt-preview"

    # AWS Models
    AWS_TTS = "generative"
    AWS_STT = "aws"

    # Gladia Models
    GLADIA_STT = "solaria-1"

    # LMNT Models
    LMNT_TTS = "aurora"

    # Azure Models
    AZURE_STT = "azure-stt"
    AZURE_TTS = "azure-tts"

    # DeepInfra Models
    DEEPINFRA_OPENCHAT_3_5 = "openchat/openchat_3.5"
    DEEPINFRA_WIZARD_LM = "microsoft/WizardLM-2-8x22B"
    DEEPINFRA_DEEPSEEK = "deepseek-ai/DeepSeek-R1"

    # GROQ Models
    GROQ_LLAMA_3_3 = "llama-3.3-70b-versatile"
    GROQ_LLAMA_3_1 = "llama-3.1-8b-instant"
    GROQ_DEEPSEEK = "deepseek-r1-distill-llama-70b"
    GROQ_120B = "openai/gpt-oss-120b"
    GROQ_20B = "openai/gpt-oss-20b"
    GROQ_META_LLAMA_4_SCOUT = "meta-llama/llama-4-scout-17b-16e-instruct"

    # Ollama Models
    OLLAMA_MISTRAL_7B = "mistral-7b"
    OLLAMA_LLAMA2 = "llama2"
    OLLAMA_CODELLAMA = "codellama"
    OLLAMA_VICUNA = "vicuna"
    OLLAMA_ORCA_MINI = "orca-mini"
    OLLAMA_LLAMA2_UNCENSORED = "llama2-uncensored"
    OLLAMA_WIZARD_VICUNA_UNCENSORED = "wizard-vicuna-uncensored"
    OLLAMA_NOUS_HERMES = "nous-hermes"
    OLLAMA_PHIND_CODELLAMA = "phind-codellama"
    OLLAMA_MISTRAL_OPENORCA = "mistral-openorca"
    OLLAMA_WIZARDCODER = "wizardcoder"
    OLLAMA_WIZARD_MATH = "wizard-math"
    OLLAMA_LLAMA2_CHINESE = "llama2-chinese"
    OLLAMA_STABLE_BELUGA = "stable-beluga"
    OLLAMA_CODEUP = "codeup"
    OLLAMA_EVERYTHINGLM = "everythinglm"
    OLLAMA_WIZARDLM_UNCENSORED = "wizardlm-uncensored"
    OLLAMA_MEDLLAMA2 = "medllama2"
    OLLAMA_FALCON = "falcon"
    OLLAMA_WIZARD_VICUNA = "wizard-vicuna"
    OLLAMA_OPEN_ORCA_PLATYPUS2 = "open-orca-platypus2"
    OLLAMA_ZEPHYR = "zephyr"
    OLLAMA_STARCODER = "starcoder"
    OLLAMA_SAMANTHA_MISTRAL = "samantha-mistral"
    OLLAMA_WIZARDLM = "wizardlm"
    OLLAMA_OPENHERMES2_MISTRAL = "openhermes2-mistral"
    OLLAMA_SQLCODER = "sqlcoder"
    OLLAMA_NEXUSRAVEN = "nexusraven"
    OLLAMA_DOLPHIN2_1_MISTRAL = "dolphin2.1-mistral"

    @classmethod
    def get_provider(cls, model_name: str) -> str:
        """Get the provider name from the model name."""
        if not isinstance(model_name, cls):
            model_name = cls(model_name)

        name = model_name.name
        if name.startswith("OPENAI_"):
            return "openai"
        elif name.startswith("ANTHROPIC_"):
            return "anthropic"
        elif name.startswith("DEEPINFRA_"):
            return "deepinfra"
        elif name.startswith("OLLAMA_"):
            return "ollama"
        else:
            return "unknown"

    @classmethod
    def from_provider(cls, provider: str) -> List["AIModelName"]:
        """Get all models for a specific provider."""
        return [model for model in cls if model.name.startswith(f"{provider.upper()}_")]

    @classmethod
    def to_pydantic_ai(cls, model_name: str) -> str:
        """Convert AIModelName to pydantic_ai KnownModelName format.

        Args:
            model_name: The model name to convert

        Returns:
            The corresponding pydantic_ai model name
        """
        if not isinstance(model_name, cls):
            model_name = cls(model_name)

        provider = cls.get_provider(model_name)

        # Mapping dictionary for special cases
        special_cases = {
            AIModelName.OPENAI_GPT4_O: "openai:gpt-4o",
            AIModelName.OPENAI_GPT4_O_MINI: "openai:gpt-4o-mini",
            AIModelName.OPENAI_GPT4_TURBO: "openai:gpt-4-turbo",
            AIModelName.OPENAI_GPT4: "openai:gpt-4",
            AIModelName.OPENAI_GPT3: "openai:gpt-3.5-turbo",
            AIModelName.OLLAMA_CODELLAMA: "ollama:codellama",
            AIModelName.OLLAMA_LLAMA2: "ollama:llama3",
            AIModelName.OLLAMA_MISTRAL_7B: "ollama:mistral",
            AIModelName.OLLAMA_STARCODER: "ollama:starcoder2",
            AIModelName.DEEPINFRA_DEEPSEEK: "deepseek-ai/DeepSeek-R1",
        }

        if model_name in special_cases:
            return special_cases[model_name]

        # Default mapping pattern
        if provider == "ollama":
            # Strip OLLAMA_ prefix and convert to lowercase
            base_name = model_name.name.replace("OLLAMA_", "").lower()
            return f"ollama:{base_name}"
        elif provider == "openai":
            # Strip OPENAI_ prefix and handle special cases
            base_name = model_name.name.replace("OPENAI_", "").lower()
            return f"openai:{base_name}"

        # For unsupported models, return test to avoid errors
        return "test"


OPEN_AI_EMBEDDING_MODELS = {
    AIModelName.OPENAI_ADA: EmbeddingModelProviderModelInfo(
        name=AIModelName.OPENAI_ADA,
        service=ModelProviderService.EMBEDDING,
        provider_name=ModelProviderName.OPENAI,
        prompt_token_cost=0.0004,
        completion_token_cost=0.0,
        max_tokens=8191,
        embedding_dimensions=1536,
    ),
}


OPEN_AI_LANGUAGE_MODELS = {
    AIModelName.OPENAI_GPT3: LanguageModelProviderModelInfo(
        name=AIModelName.OPENAI_GPT3,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.OPENAI,
        prompt_token_cost=0.0015,
        completion_token_cost=0.002,
        max_tokens=4096,
    ),
    AIModelName.OPENAI_GPT3_FINETUNE: LanguageModelProviderModelInfo(
        name=AIModelName.OPENAI_GPT3_FINETUNE,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.OPENAI,
        prompt_token_cost=0.0015,
        completion_token_cost=0.002,
        max_tokens=4096,
    ),
    AIModelName.OPENAI_GPT3_16K: LanguageModelProviderModelInfo(
        name=AIModelName.OPENAI_GPT3_16K,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.OPENAI,
        prompt_token_cost=0.003,
        completion_token_cost=0.002,
        max_tokens=16384,
    ),
    AIModelName.OPENAI_GPT4: LanguageModelProviderModelInfo(
        name=AIModelName.OPENAI_GPT4,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.OPENAI,
        prompt_token_cost=0.03,
        completion_token_cost=0.06,
        max_tokens=8192,
    ),
    AIModelName.OPENAI_GPT4_32K: LanguageModelProviderModelInfo(
        name=AIModelName.OPENAI_GPT4_32K,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.OPENAI,
        prompt_token_cost=0.06,
        completion_token_cost=0.12,
        max_tokens=32768,
    ),
    AIModelName.OPENAI_GPT4_TURBO: LanguageModelProviderModelInfo(
        name=AIModelName.OPENAI_GPT4_TURBO,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.OPENAI,
        prompt_token_cost=0.06,
        completion_token_cost=0.12,
        max_tokens=4096,
    ),
    AIModelName.OPENAI_GPT4_VISION: LanguageModelProviderModelInfo(
        name=AIModelName.OPENAI_GPT4_VISION,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.OPENAI,
        prompt_token_cost=0.0006,
        completion_token_cost=0.0012,
        max_tokens=4096,
    ),
    AIModelName.OPENAI_GPT4_O: LanguageModelProviderModelInfo(
        name=AIModelName.OPENAI_GPT4_O,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.OPENAI,
        prompt_token_cost=0.002,  # $2.00 per 1M tokens
        completion_token_cost=0.008,  # $8.00 per 1M tokens
        max_tokens=4096,
    ),
    AIModelName.OPENAI_GPT4_O_MINI: LanguageModelProviderModelInfo(
        name=AIModelName.OPENAI_GPT4_O_MINI,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.OPENAI,
        prompt_token_cost=0.0004,  # $0.40 per 1M tokens
        completion_token_cost=0.0016,  # $1.60 per 1M tokens
        max_tokens=16384,
    ),
    AIModelName.OPENAI_O3_MINI: LanguageModelProviderModelInfo(
        name=AIModelName.OPENAI_O3_MINI,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.OPENAI,
        prompt_token_cost=0.0011,  # $1.10 per 1M tokens
        completion_token_cost=0.0044,  # $4.40 per 1M tokens
        max_tokens=4096,
    ),
    AIModelName.OPENAI_REALTIME: LanguageModelProviderModelInfo(
        name=AIModelName.OPENAI_REALTIME,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.OPENAI,
        prompt_token_cost=0.005,  # $5.00 per 1M tokens
        completion_token_cost=0.020,  # $20.00 per 1M tokens
        max_tokens=4096,
    ),
    AIModelName.OPENAI_GPT_5o: LanguageModelProviderModelInfo(
        name=AIModelName.OPENAI_GPT_5o,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.OPENAI,
        prompt_token_cost=1.25,
        completion_token_cost=10,
        max_tokens=1000000,
    ),
    AIModelName.OPENAI_GPT_5o_mini : LanguageModelProviderModelInfo(
        name=AIModelName.OPENAI_GPT_5o_mini,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.OPENAI,
        prompt_token_cost=0.250,
        completion_token_cost=2,
        max_tokens=1000000,
    )
}


OPEN_AI_MODELS = {
    **OPEN_AI_LANGUAGE_MODELS,
    **OPEN_AI_EMBEDDING_MODELS,
}


ANTHROPIC_EMBEDDING_MODELS = {
    AIModelName.ANTHROPIC_CLAUDE2: EmbeddingModelProviderModelInfo(
        name=AIModelName.ANTHROPIC_CLAUDE2,
        service=ModelProviderService.EMBEDDING,
        provider_name=ModelProviderName.ANTHROPIC,
        prompt_token_cost=0.0004,
        completion_token_cost=0.0,
        max_tokens=100000,
        embedding_dimensions=1536,
    ),
}


ANTHROPIC_LANGUAGE_MODELS = {
    AIModelName.ANTHROPIC_CLAUDE3_SONNET: LanguageModelProviderModelInfo(
        name=AIModelName.ANTHROPIC_CLAUDE3_SONNET,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.ANTHROPIC,
        prompt_token_cost=0.00015,
        completion_token_cost=0.002,
        max_tokens=200000,
    ),
    AIModelName.ANTHROPIC_CLAUDE_SONNET_4: LanguageModelProviderModelInfo(
        name=AIModelName.ANTHROPIC_CLAUDE_SONNET_4,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.ANTHROPIC,
        prompt_token_cost=0.003,  # $3.00 per 1M tokens
        completion_token_cost=0.015,  # $15.00 per 1M tokens
        max_tokens=200000,
    ),
    AIModelName.ANTHROPIC_CLAUDE3_OPUS: LanguageModelProviderModelInfo(
        name=AIModelName.ANTHROPIC_CLAUDE3_OPUS,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.ANTHROPIC,
        prompt_token_cost=0.00015,
        completion_token_cost=0.002,
        max_tokens=200000,
    ),
    AIModelName.ANTHROPIC_CLAUDE3_HAIKU: LanguageModelProviderModelInfo(
        name=AIModelName.ANTHROPIC_CLAUDE3_HAIKU,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.ANTHROPIC,
        prompt_token_cost=0.00015,
        completion_token_cost=0.002,
        max_tokens=200000,
    ),
    AIModelName.ANTHROPIC_CLAUDE2_1: LanguageModelProviderModelInfo(
        name=AIModelName.ANTHROPIC_CLAUDE2_1,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.ANTHROPIC,
        prompt_token_cost=0.0015,
        completion_token_cost=0.002,
        max_tokens=200000,
    ),
    AIModelName.ANTHROPIC_CLAUDE2: LanguageModelProviderModelInfo(
        name=AIModelName.ANTHROPIC_CLAUDE2,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.ANTHROPIC,
        prompt_token_cost=0.0015,
        completion_token_cost=0.002,
        max_tokens=100000,
    ),
    AIModelName.ANTHROPIC_CLAUDE2_FULL: LanguageModelProviderModelInfo(
        name=AIModelName.ANTHROPIC_CLAUDE2_FULL,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.ANTHROPIC,
        prompt_token_cost=0.003,
        completion_token_cost=0.002,
        max_tokens=100000,
    ),
    AIModelName.ANTHROPIC_CLAUDE2_INSTANT: LanguageModelProviderModelInfo(
        name=AIModelName.ANTHROPIC_CLAUDE2_INSTANT,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.ANTHROPIC,
        prompt_token_cost=0.03,
        completion_token_cost=0.06,
        max_tokens=100000,
    ),
    AIModelName.ANTHROPIC_CLAUDE2_INSTANT_FULL: LanguageModelProviderModelInfo(
        name=AIModelName.ANTHROPIC_CLAUDE2_INSTANT_FULL,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.ANTHROPIC,
        prompt_token_cost=0.06,
        completion_token_cost=0.12,
        max_tokens=100000,
    ),
}


ANTHROPIC_MODELS = {
    **ANTHROPIC_LANGUAGE_MODELS,
    **ANTHROPIC_EMBEDDING_MODELS,
}



GROQ_LANGUAGE_MODELS = {
    AIModelName.GROQ_LLAMA_3_3: LanguageModelProviderModelInfo(
        name=AIModelName.GROQ_LLAMA_3_3,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.GROQ,
        prompt_token_cost=0.00059,  # $0.59 per 1M tokens
        completion_token_cost=0.00079,  # $0.79 per 1M tokens
        max_tokens=4096,
    ),
    AIModelName.GROQ_LLAMA_3_1: LanguageModelProviderModelInfo(
        name=AIModelName.GROQ_LLAMA_3_1,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.GROQ,
        prompt_token_cost=0.00005,  # $0.05 per 1M tokens
        completion_token_cost=0.00008,  # $0.08 per 1M tokens
        max_tokens=4096,
    ),
    AIModelName.GROQ_120B: LanguageModelProviderModelInfo(
        name=AIModelName.GROQ_120B,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.GROQ,
        prompt_token_cost=0.002,  # $2.00 per 1M tokens
        completion_token_cost=0.008,  # $8.00 per 1M tokens
        max_tokens=8192,
    ),
    AIModelName.GROQ_20B: LanguageModelProviderModelInfo(
        name=AIModelName.GROQ_20B,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.GROQ,
        prompt_token_cost=0.00059,  # $0.59 per 1M tokens
        completion_token_cost=0.00079,  # $0.79 per 1M tokens
        max_tokens=8192,
    ),
    AIModelName.GROQ_META_LLAMA_4_SCOUT: LanguageModelProviderModelInfo(
        name=AIModelName.GROQ_META_LLAMA_4_SCOUT,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.GROQ,
        prompt_token_cost=0.00059,  # $0.59 per 1M tokens
        completion_token_cost=0.00079,  # $0.79 per 1M tokens
        max_tokens=8192,
    ),
}

GROQ_MODELS = {
    **GROQ_LANGUAGE_MODELS,
}

DEEP_INFRA_EMBEDDING_MODELS = {}


DEEP_INFRA_LANGUAGE_MODELS = {
    AIModelName.DEEPINFRA_OPENCHAT_3_5: LanguageModelProviderModelInfo(
        name=AIModelName.DEEPINFRA_OPENCHAT_3_5,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.DEEPINFRA,
        prompt_token_cost=0.003,
        completion_token_cost=0.002,
        max_tokens=8132,
    ),
    AIModelName.DEEPINFRA_WIZARD_LM: LanguageModelProviderModelInfo(
        name=AIModelName.DEEPINFRA_WIZARD_LM,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.DEEPINFRA,
        prompt_token_cost=0.0006,
        completion_token_cost=0.0006,
        max_tokens=65536,
    ),
}


DEEP_INFRA_MODELS = {
    **DEEP_INFRA_LANGUAGE_MODELS,
    **DEEP_INFRA_EMBEDDING_MODELS,
}


OLLAMA_EMBEDDING_MODELS = {
    AIModelName.OLLAMA_MISTRAL_7B: EmbeddingModelProviderModelInfo(
        name=AIModelName.OLLAMA_MISTRAL_7B,
        service=ModelProviderService.EMBEDDING,
        provider_name=ModelProviderName.OLLAMA,
        prompt_token_cost=0.0004,
        completion_token_cost=0.0,
        max_tokens=100000,
        embedding_dimensions=1536,
    ),
}

OLLAMA_LANGUAGE_MODELS = {
    AIModelName.OLLAMA_MISTRAL_7B: LanguageModelProviderModelInfo(
        name=AIModelName.OLLAMA_MISTRAL_7B,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.OLLAMA,
        prompt_token_cost=0.0015,  # Placeholder
        completion_token_cost=0.002,  # Placeholder
        max_tokens=100000,  # Placeholder
    ),
    AIModelName.OLLAMA_LLAMA2: LanguageModelProviderModelInfo(
        name=AIModelName.OLLAMA_LLAMA2,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.OLLAMA,
        prompt_token_cost=0.0015,  # Placeholder
        completion_token_cost=0.002,  # Placeholder
        max_tokens=100000,  # Placeholder
    ),
    AIModelName.OLLAMA_WIZARD_MATH: LanguageModelProviderModelInfo(
        name=AIModelName.OLLAMA_WIZARD_MATH,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.OLLAMA,
        prompt_token_cost=0.0015,  # Placeholder
        completion_token_cost=0.002,  # Placeholder
        max_tokens=100000,  # Placeholder
    ),
}

GOOGLE_MODELS ={
    AIModelName.GEMINI_FLASH_2_Lite : LanguageModelProviderModelInfo(
        name=AIModelName.GEMINI_FLASH_2_Lite,
        service=ModelProviderService.LANGUAGE,
        provider_name=ModelProviderName.GOOGLE,
        prompt_token_cost=0.10,
        completion_token_cost=0.40,
        max_tokens=1000000,
    )
}

OLLAMA_MODELS = {
    **OLLAMA_LANGUAGE_MODELS,
    **OLLAMA_EMBEDDING_MODELS,
}

AI_MODELS = {
    **OPEN_AI_MODELS,
    **ANTHROPIC_MODELS,
    **OLLAMA_MODELS,
    **DEEP_INFRA_MODELS,
    **GROQ_MODELS,
    **GOOGLE_MODELS
}

AI_EMBEDDING_MODELS = {**OPEN_AI_EMBEDDING_MODELS}

# Voice Model Pricing for STT and TTS models
# Pricing structure: audio_cost per audio_per seconds (for STT) or character_per characters (for TTS)
VOICE_MODEL_PRICING = {
    # STT Models - cost per 60 seconds of audio
    AIModelName.OPENAI_WHISPER_1: {"audio_cost": 0.006, "audio_per": 60},
    AIModelName.OPENAI_GPT4O_TRANSCRIBE: {"audio_cost": 0.06, "audio_per": 60},
    AIModelName.DEEPGRAM_NOVA_2_GENERAL: {"audio_cost": 0.0058, "audio_per": 60},
    AIModelName.DEEPGRAM_NOVA_3_GENERAL: {"audio_cost": 0.0058, "audio_per": 60},
    AIModelName.DEEPGRAM_NOVA_3: {"audio_cost": 0.0058, "audio_per": 60},
    AIModelName.GOOGLE_CHIRP: {"audio_cost": 0.012, "audio_per": 60},
    AIModelName.GOOGLE_CHIRP_2: {"audio_cost": 0.012, "audio_per": 60},
    AIModelName.GOOGLE_TELEPHONY: {"audio_cost": 0.012, "audio_per": 60},
    AIModelName.SARVAM_STT: {"audio_cost": 0.0056, "audio_per": 60},
    AIModelName.SONIOX_STT: {"audio_cost": 0.0058, "audio_per": 60},
    AIModelName.AWS_STT: {"audio_cost": 0.012, "audio_per": 60},
    AIModelName.GLADIA_STT: {"audio_cost": 0.0058, "audio_per": 60},
    AIModelName.AZURE_STT: {"audio_cost": 0.012, "audio_per": 60},
    AIModelName.NOVA_3_DEEPGRAM :{"audio_cost": 0.0092,"audio_per": 60 },

    # TTS Models - cost per characters
    AIModelName.SONIC_2_CARTESIA:{"audio_cost": 5, "character_per": 1000000},
    AIModelName.OPENAI_TTS_1: {"audio_cost": 15, "character_per": 1000000},
    AIModelName.OPENAI_TTS_1_HD: {"audio_cost": 30, "character_per": 1000000},
    AIModelName.DEEPGRAM_AURA_HELIOS_EN: {"audio_cost": 0.030, "character_per": 1000},
    AIModelName.DEEPGRAM_AURA_LUNA_EN: {"audio_cost": 0.030, "character_per": 1000},
    AIModelName.DEEPGRAM_AURA_ATHENA_EN: {"audio_cost": 0.030, "character_per": 1000},
    AIModelName.DEEPGRAM_AURA_ASTERIA_EN: {"audio_cost": 0.030, "character_per": 1000},
    AIModelName.DEEPGRAM_AURA_ARCANIS_EN: {"audio_cost": 0.030, "character_per": 1000},
    AIModelName.ELEVENLABS_ELEVEN_FLASH_V2_5: {"audio_cost": 0.15, "character_per": 1000},
    AIModelName.ELEVENLABS_ELEVEN_MULTILINGUAL_V2: {"audio_cost": 0.30, "character_per": 1000},
    AIModelName.CARTESIA_SONIC: {"audio_cost": 0.18, "character_per": 10000},
    AIModelName.CARTESIA_SONIC_2: {"audio_cost": 0.18, "character_per": 10000},
    AIModelName.CARTESIA_SONIC_TURBO: {"audio_cost": 0.18, "character_per": 10000},
    AIModelName.SARVAM_TTS: {"audio_cost": 0.18, "character_per": 10000},
    AIModelName.LMNT_TTS: {"audio_cost": 15, "character_per": 1000000},
    AIModelName.AWS_TTS: {"audio_cost": 0.015, "character_per": 1000},
    AIModelName.AZURE_TTS: {"audio_cost": 0.015, "character_per": 1000},
}
