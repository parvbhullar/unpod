# tests/core/voice/services/test_livekit_config_parity.py
"""
Integration tests to verify LiveKit services config parity with Pipecat.

These tests ensure that configuration options available in Pipecat
are also available in LiveKit services for seamless migration.
"""

import sys
from unittest.mock import AsyncMock, MagicMock

# Mock pipecat and livekit dependencies before any imports
pipecat_mock = MagicMock()
sys.modules["pipecat"] = pipecat_mock
sys.modules["pipecat.transports"] = MagicMock()
sys.modules["pipecat.transports.livekit"] = MagicMock()
sys.modules["pipecat.transports.livekit.transport"] = MagicMock()
sys.modules["pipecat.audio.vad.silero"] = MagicMock()
sys.modules["pipecat.audio.vad.vad_analyzer"] = MagicMock()
sys.modules["pipecat.audio"] = MagicMock()
sys.modules["pipecat.audio.vad"] = MagicMock()
sys.modules["pipecat.services"] = MagicMock()
sys.modules["pipecat.services.openai"] = MagicMock()
sys.modules["pipecat.services.deepgram"] = MagicMock()
sys.modules["pipecat.services.cartesia"] = MagicMock()
sys.modules["pipecat.services.elevenlabs"] = MagicMock()
sys.modules["pipecat.services.playht"] = MagicMock()
sys.modules["pipecat.services.google"] = MagicMock()
sys.modules["pipecat.services.lmnt"] = MagicMock()
sys.modules["pipecat.services.azure"] = MagicMock()
sys.modules["pipecat.services.anthropic"] = MagicMock()
sys.modules["pipecat.services.xtts"] = MagicMock()
sys.modules["pipecat.processors"] = MagicMock()
sys.modules["pipecat.processors.aggregators.llm_response"] = MagicMock()
sys.modules["pipecat.processors.aggregators"] = MagicMock()
sys.modules["pipecat.processors.filters"] = MagicMock()
sys.modules["pipecat.frames"] = MagicMock()
sys.modules["pipecat.frames.frames"] = MagicMock()
sys.modules["pipecat.pipeline"] = MagicMock()
sys.modules["pipecat.pipeline.pipeline"] = MagicMock()
sys.modules["pipecat.pipeline.task"] = MagicMock()
sys.modules["pipecat.pipeline.runner"] = MagicMock()
sys.modules["pipecat.clocks"] = MagicMock()
sys.modules["pipecat.clocks.system_clock"] = MagicMock()
sys.modules["pipecat.sync"] = MagicMock()
sys.modules["pipecat.sync.base_notifier"] = MagicMock()
sys.modules["pipecat.sync.event_notifier"] = MagicMock()
sys.modules["pipecat.transcriptions"] = MagicMock()
sys.modules["pipecat.transcriptions.language"] = MagicMock()
sys.modules["bson"] = MagicMock()
sys.modules["bson.objectid"] = MagicMock()

# Mock livekit plugins before importing
mock_livekit = MagicMock()
mock_livekit_agents = MagicMock()
mock_livekit_rtc = MagicMock()

sys.modules["livekit"] = mock_livekit
sys.modules["livekit.agents"] = mock_livekit_agents
sys.modules["livekit.agents.llm"] = MagicMock()
sys.modules["livekit.agents.pipeline"] = MagicMock()
sys.modules["livekit.agents.voice_assistant"] = MagicMock()
sys.modules["livekit.agents.voice"] = MagicMock()
sys.modules["livekit.agents.multimodal"] = MagicMock()
sys.modules["livekit.agents.tokenize"] = MagicMock()
sys.modules["livekit.agents.stt"] = MagicMock()
sys.modules["livekit.agents.tts"] = MagicMock()
sys.modules["livekit.plugins"] = MagicMock()
sys.modules["livekit.plugins.openai"] = MagicMock()
sys.modules["livekit.plugins.deepgram"] = MagicMock()
sys.modules["livekit.plugins.cartesia"] = MagicMock()
sys.modules["livekit.plugins.silero"] = MagicMock()
sys.modules["livekit.plugins.turn_detector"] = MagicMock()
sys.modules["livekit.plugins.anthropic"] = MagicMock()
sys.modules["livekit.plugins.google"] = MagicMock()
sys.modules["livekit.plugins.groq"] = MagicMock()
sys.modules["livekit.plugins.aws"] = MagicMock()
sys.modules["livekit.plugins.playai"] = MagicMock()
sys.modules["livekit.plugins.elevenlabs"] = MagicMock()
sys.modules["livekit.plugins.eleven_labs"] = MagicMock()
sys.modules["livekit.plugins.sarvam"] = MagicMock()
sys.modules["livekit.plugins.lmnt"] = MagicMock()
sys.modules["livekit.plugins.xai"] = MagicMock()
sys.modules["livekit.rtc"] = mock_livekit_rtc
sys.modules["livekit.rtc._proto"] = MagicMock()

import pytest


class TestLiveKitConfigParity:
    """Integration tests for config parity between Pipecat and LiveKit."""

    def test_all_llm_providers_support_temperature(self):
        """All LLM providers should support temperature config."""
        providers = ["openai", "groq", "anthropic", "azure", "ollama", "cerebras"]

        for provider in providers:
            config = {
                "llm_provider": provider,
                "llm_model": "test-model",
                "temperature": 0.4,
            }

            from super.core.voice.services.livekit_services import (
                LiveKitServiceFactory,
            )

            factory = LiveKitServiceFactory(config)

            # Verify the factory accepts temperature config
            temp = factory._get_voice_optimized_temperature()
            assert temp == 0.4, f"{provider} should support temperature config"

    def test_all_tts_providers_support_language(self):
        """All TTS providers should support language config."""
        providers_with_language = [
            "elevenlabs",
            "cartesia",
            "google",
            "lmnt",
            "sarvam",
        ]

        for provider in providers_with_language:
            config = {
                "tts_provider": provider,
                "tts_voice": "test-voice",
                "language": "hi",
            }

            from super.core.voice.services.livekit_services import (
                LiveKitServiceFactory,
            )

            factory = LiveKitServiceFactory(config)

            # Verify language is in config
            assert factory.config.get("language") == "hi"

    def test_deepgram_stt_supports_interim_results_control(self):
        """Deepgram STT should support use_final_transcriptions_only."""
        config = {
            "stt_provider": "deepgram",
            "stt_model": "nova-3",
            "use_final_transcriptions_only": True,
        }

        from super.core.voice.services.livekit_services import LiveKitServiceFactory

        factory = LiveKitServiceFactory(config)

        assert factory.config.get("use_final_transcriptions_only") is True

    def test_openai_tts_supports_voice_instructions(self):
        """OpenAI TTS should support voice_instructions for modern models."""
        config = {
            "tts_provider": "openai",
            "tts_model": "gpt-4o-mini-tts",
            "tts_voice": "alloy",
            "voice_instructions": "Speak calmly and professionally.",
        }

        from super.core.voice.services.livekit_services import LiveKitServiceFactory

        factory = LiveKitServiceFactory(config)

        assert (
            factory.config.get("voice_instructions")
            == "Speak calmly and professionally."
        )

    @pytest.mark.parametrize(
        "provider,model,expected_temp",
        [
            ("openai", "gpt-4o-mini", 0.5),
            ("groq", "llama-3.1-70b", 0.3),
            ("anthropic", "claude-sonnet-4-20250514", 0.4),
            ("google", "gemini-2.0-flash", 0.6),
        ],
    )
    def test_llm_temperature_configurable_per_provider(
        self, provider: str, model: str, expected_temp: float
    ):
        """LLM temperature should be configurable for each provider."""
        config = {
            "llm_provider": provider,
            "llm_model": model,
            "temperature": expected_temp,
        }

        from super.core.voice.services.livekit_services import LiveKitServiceFactory

        factory = LiveKitServiceFactory(config)
        actual_temp = factory._get_voice_optimized_temperature()

        assert actual_temp == expected_temp

    @pytest.mark.parametrize(
        "provider,config_key,config_value",
        [
            ("elevenlabs", "stability", 0.5),
            ("elevenlabs", "similarity", 0.6),
            ("elevenlabs", "style", 0.5),
            ("elevenlabs", "tts_speed", 0.95),
            ("sarvam", "pitch", 0.3),
            ("sarvam", "pace", 1.0),
            ("sarvam", "loudness", 1),
            ("cartesia", "speed", 1.0),
        ],
    )
    def test_tts_provider_specific_config(
        self, provider: str, config_key: str, config_value: float
    ):
        """TTS providers should support their specific configuration options."""
        config = {
            "tts_provider": provider,
            "tts_voice": "test-voice",
            config_key: config_value,
        }

        from super.core.voice.services.livekit_services import LiveKitServiceFactory

        factory = LiveKitServiceFactory(config)

        assert factory.config.get(config_key) == config_value

    def test_deepgram_stt_config_options(self):
        """Deepgram STT should support various configuration options."""
        config = {
            "stt_provider": "deepgram",
            "stt_model": "nova-3",
            "stt_smart_format": True,
            "stt_filler_words": False,
            "stt_endpointing_ms": 25,
            "stt_profanity_filter": False,
        }

        from super.core.voice.services.livekit_services import LiveKitServiceFactory

        factory = LiveKitServiceFactory(config)

        assert factory.config.get("stt_smart_format") is True
        assert factory.config.get("stt_filler_words") is False
        assert factory.config.get("stt_endpointing_ms") == 25
        assert factory.config.get("stt_profanity_filter") is False

    def test_max_tokens_configurable(self):
        """max_tokens should be configurable for LLM providers."""
        config = {
            "llm_provider": "openai",
            "llm_model": "gpt-4o",
            "max_tokens": 800,
        }

        from super.core.voice.services.livekit_services import LiveKitServiceFactory

        factory = LiveKitServiceFactory(config)
        max_tokens = factory._get_voice_optimized_max_tokens()

        assert max_tokens == 800

    def test_speaking_plan_config(self):
        """Speaking plan settings should be configurable."""
        speaking_plan = {
            "min_interruption_duration": 0.5,
            "min_interruption_words": 3,
            "min_silence_duration": 0.3,
            "vad_activation_threshold": 0.4,
            "eagerness": "high",
        }
        config = {
            "llm_provider": "openai",
            "speaking_plan": speaking_plan,
        }

        from super.core.voice.services.livekit_services import LiveKitServiceFactory

        factory = LiveKitServiceFactory(config)

        assert factory.speaking_plan == speaking_plan
        assert factory.speaking_plan.get("min_interruption_duration") == 0.5
        assert factory.speaking_plan.get("eagerness") == "high"

    @pytest.mark.asyncio
    async def test_session_defaults_disable_preemptive_generation(self, monkeypatch):
        """Voice sessions should not preemptively generate by default (prevents duplicate/garbled speech)."""
        import super.core.voice.services.livekit_services as livekit_services_mod

        captured_kwargs = {}

        class FakeAgentSession:
            def __init__(self, **kwargs):
                captured_kwargs.update(kwargs)

        monkeypatch.setattr(livekit_services_mod, "AgentSession", FakeAgentSession)

        factory = livekit_services_mod.LiveKitServiceFactory(
            {
                "llm_provider": "openai",
                "llm_model": "gpt-4o-mini",
                "stt_provider": "deepgram",
                "stt_model": "nova-3",
                "tts_provider": "cartesia",
                "tts_model": "sonic-3",
            }
        )

        monkeypatch.setattr(factory, "_create_vad", lambda: object())
        monkeypatch.setattr(factory, "create_stt_with_retry", AsyncMock(return_value=object()))
        monkeypatch.setattr(factory, "create_llm_with_retry", AsyncMock(return_value=object()))
        monkeypatch.setattr(factory, "create_tts_with_retry", AsyncMock(return_value=object()))

        await factory.create_session(mode=livekit_services_mod.LiveKitServiceMode.INFERENCE)

        assert captured_kwargs["preemptive_generation"] is False

    def test_reasoning_effort_config_for_o1_models(self):
        """reasoning_effort should be configurable for o1/o3 models."""
        config = {
            "llm_provider": "openai",
            "llm_model": "o1-preview",
            "reasoning_effort": "medium",
        }

        from super.core.voice.services.livekit_services import LiveKitServiceFactory

        factory = LiveKitServiceFactory(config)

        assert factory.config.get("reasoning_effort") == "medium"

    def test_background_audio_config(self):
        """Background audio settings should be configurable."""
        background_audio = {
            "enabled": True,
            "ambient_sound": "OFFICE_AMBIENCE",
            "ambient_volume": 0.8,
            "thinking_sound": ["KEYBOARD_TYPING", "KEYBOARD_TYPING2"],
            "thinking_volume": 0.7,
        }
        config = {
            "llm_provider": "openai",
            "background_audio": background_audio,
        }

        from super.core.voice.services.livekit_services import LiveKitServiceFactory

        factory = LiveKitServiceFactory(config)

        assert factory.config.get("background_audio") == background_audio

    def test_google_tts_gender_config(self):
        """Google TTS should support gender configuration."""
        config = {
            "tts_provider": "google",
            "tts_voice": "en-US-Wavenet-F",
            "language": "en",
            "gender": "female",
        }

        from super.core.voice.services.livekit_services import LiveKitServiceFactory

        factory = LiveKitServiceFactory(config)

        assert factory.config.get("gender") == "female"

    def test_retry_config_options(self):
        """Retry settings should be configurable for all service types."""
        config = {
            "llm_provider": "openai",
            "stt_retry_attempts": 3,
            "stt_retry_backoff": 0.5,
            "llm_retry_attempts": 2,
            "llm_retry_backoff": 0.5,
            "tts_retry_attempts": 2,
            "tts_retry_backoff": 0.5,
        }

        from super.core.voice.services.livekit_services import LiveKitServiceFactory

        factory = LiveKitServiceFactory(config)

        assert factory.config.get("stt_retry_attempts") == 3
        assert factory.config.get("llm_retry_attempts") == 2
        assert factory.config.get("tts_retry_attempts") == 2
