import asyncio

import pytest

from tests.core.voice.helpers.runtime_imports import prepare_runtime_imports


def _load_voice_agent_handler_module():
    prepare_runtime_imports()
    import super.core.voice.voice_agent_handler as vah

    return vah


def test_service_cache_keying_and_stale_cleanup() -> None:
    vah = _load_voice_agent_handler_module()
    cache = vah.ServiceCache()
    cfg = {"stt_provider": "deepgram", "stt_model": "nova-3", "language": "hi"}

    cache.set_stt(cfg, object())
    assert cache.get_stt(cfg) is not None

    for i in range(20):
        cache._stt_cache[f"k-{i}"] = object()

    cleared = cache.clear_stale_services(max_services=5)
    assert cleared > 0
    assert len(cache._stt_cache) <= 5


def test_service_cache_clear_all_resets_timing_metrics() -> None:
    vah = _load_voice_agent_handler_module()
    cache = vah.ServiceCache()
    cache.silero_vad = object()
    cache.vad_load_time_ms = 321.0
    cache.is_vad_loaded = True
    cache.set_embedding_fn(object(), load_time_ms=123.0)

    cache.clear_all()

    assert cache.vad_load_time_ms == 0.0
    assert cache.embedding_load_time_ms == 0.0


@pytest.mark.asyncio
async def test_cancel_pending_tasks_cancels_all_live_tasks() -> None:
    vah = _load_voice_agent_handler_module()
    handler = vah.VoiceAgentHandler(session_id="t-1")

    async def sleeper() -> None:
        await asyncio.sleep(10)

    task = handler._track_task(asyncio.create_task(sleeper()))
    cancelled = await handler._cancel_pending_tasks(timeout=0.1)

    assert cancelled >= 1
    assert task.cancelled() or task.done()
    assert len(handler._pending_tasks) == 0
