import pytest

from tests.core.voice.helpers.runtime_imports import prepare_runtime_imports


def _load_voice_agent_handler_module():
    prepare_runtime_imports()
    import super.core.voice.voice_agent_handler as vah

    return vah


def test_merge_executor_config_prioritizes_executor_values() -> None:
    vah = _load_voice_agent_handler_module()
    handler = vah.VoiceAgentHandler(session_id="t-2")
    handler.config = {
        "stt_provider": "deepgram",
        "stt_model": "nova-3",
        "telephony": {"krisp": True},
    }

    merged = handler._merge_executor_config(
        {"stt_provider": "whisper", "telephony": {"krisp": False}}
    )

    assert merged["stt_provider"] == "deepgram"
    assert merged["telephony"]["krisp"] is True


@pytest.mark.asyncio
async def test_resolve_space_id_background_sets_space_id_once(monkeypatch) -> None:
    vah = _load_voice_agent_handler_module()
    handler = vah.VoiceAgentHandler(session_id="t-3")
    user_data = {}

    async def fake_to_thread(func, token):
        return 1057

    monkeypatch.setattr(vah.asyncio, "to_thread", fake_to_thread)

    await handler._resolve_space_id_background(user_data, "SPACE_TOKEN")

    assert user_data["space_id"] == 1057


@pytest.mark.asyncio
async def test_get_config_with_cache_handles_uninitialized_temp_perf_logs(monkeypatch) -> None:
    vah = _load_voice_agent_handler_module()
    handler = vah.VoiceAgentHandler(session_id="t-4")
    handler._temp_perf_logs = None

    from super_services.voice.models import config as config_module

    monkeypatch.setattr(
        config_module.ModelConfig,
        "get_config",
        lambda _self, _agent_handle: {
            "agent_id": "demo-agent",
            "stt_provider": "deepgram",
        },
    )

    config = await handler._get_config_with_cache(agent_handle="demo-agent")

    assert config["agent_id"] == "demo-agent"
    assert isinstance(handler._temp_perf_logs, list)
    assert any(item.get("name") == "merger_config" for item in handler._temp_perf_logs)
