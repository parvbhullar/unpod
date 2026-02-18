from livekit.agents import AgentSession, inference
from enum import Enum

from super.core.voice.services.service_common import (
    ASSEMBLYAI_UNSUPPORTED_LANGUAGES,
    DEFAULT_TTS_PROVIDER,
)


class STTProviders(str, Enum):
    assemblyai = "assemblyai"
    cartesia = "cartesia"
    deepgram = "deepgram"


class TTSProviders(str, Enum):
    cartesia = "cartesia"
    elevenlabs = "elevenlabs"
    inworld = "inworld"
    rime = "rime"
    unpod = DEFAULT_TTS_PROVIDER


class LLMProviders(str, Enum):
    assemblyai = "assemblyai"
    deepseek = "deepseek-ai"
    google = "google"
    moonshotai = "moonshotai"
    openai = "openai"
    qwen = "qwen"


class InferenceFactory:
    def __init__(self, model_config=None):
        self.mode_config = model_config

    def _get_stt_model(self, model_config):
        provider = model_config.get("stt_provider")
        model = model_config.get("stt_model")
        language = model_config.get("language", "en")

        if provider not in STTProviders._value2member_map_:
            raise ValueError(
                f"Invalid STT provider '{provider}'. "
                f"Valid providers: {[p.value for p in STTProviders]}"
            )

        # AssemblyAI streaming doesn't support certain languages;
        # omit language to let the multilingual model auto-detect
        if provider == "assemblyai" and language in ASSEMBLYAI_UNSUPPORTED_LANGUAGES:
            language = None

        stt = inference.STT(
            model=f"{provider}/{model}",
            language=language,
        )

        return stt

    def _get_tts_model(self, model_config):
        provider = model_config.get("tts_provider")
        model = model_config.get("tts_model")
        language = model_config.get("language", "en")
        voice = model_config.get("voice")

        if provider not in TTSProviders._value2member_map_:
            raise ValueError(
                f"Invalid STT provider '{provider}'. "
                f"Valid providers: {[p.value for p in TTSProviders]}"
            )

        tts = inference.TTS(
            model=f"{provider}/{model}",
            language=language,
            voice=voice,
        )

        return tts

    def _get_llm_model(self, model_config):
        provider = model_config.get("llm_provider")
        model = model_config.get("llm_model")

        if provider not in LLMProviders._value2member_map_:
            raise ValueError(
                f"Invalid STT provider '{provider}'. "
                f"Valid providers: {[p.value for p in LLMProviders]}"
            )
        llm = inference.LLM(model=f"{provider}/{model}", provider=provider)

        return llm

    def create_agent_session(self, ctx, user_state):
        from livekit.plugins import silero

        model_config = user_state.model_config or {}
        speaking_plan = model_config.get("speaking_plan", {})

        vad = silero.VAD.load(
            min_silence_duration=speaking_plan.get("min_silence_duration", 0.2),
            activation_threshold=0.3,
        )

        userdata = {
            "token": user_state.token,
            "knowledge_base": user_state.knowledge_base,
            "ctx_room": ctx.room,
        }

        model_config = user_state.model_config

        if not model_config:
            AgentSession(
                userdata=userdata,
                vad=vad,
            )

        session = AgentSession(
            userdata=userdata,
            stt=self._get_stt_model(model_config),
            tts=self._get_tts_model(model_config),
            llm=self._get_llm_model(model_config),
            vad=vad,
        )

        return session
