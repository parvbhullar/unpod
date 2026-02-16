from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.core.voice.helpers.runtime_imports import prepare_runtime_imports


def _load_lite_handler_module():
    prepare_runtime_imports(lite_handler_safe=True)
    import super.core.voice.livekit.lite_handler as lkh

    return lkh


def test_goodbye_intent_detection_is_precise() -> None:
    lkh = _load_lite_handler_module()
    handler = lkh.LiveKitLiteHandler(session_id="id")

    assert handler._is_goodbye_intent("okay bye") is True
    assert handler._is_goodbye_intent("okay, tell me more") is False


@pytest.mark.asyncio
async def test_idle_disconnect_sdk_skips_post_call(monkeypatch) -> None:
    lkh = _load_lite_handler_module()
    handler = lkh.LiveKitLiteHandler(session_id="id")

    handler.user_state = MagicMock(
        extra_data={"call_type": "sdk"},
        call_status=None,
        end_time=None,
    )
    handler._session = MagicMock(generate_reply=AsyncMock())
    handler.end_call = AsyncMock()
    handler._job_context = None

    build_call_result_mock = AsyncMock()
    trigger_post_call_mock = AsyncMock()
    monkeypatch.setattr(lkh, "build_call_result", build_call_result_mock)
    monkeypatch.setattr(lkh, "trigger_post_call", trigger_post_call_mock)

    async def no_sleep(_seconds):
        return None

    monkeypatch.setattr(lkh.asyncio, "sleep", no_sleep)

    await handler._handle_idle_disconnect()

    build_call_result_mock.assert_not_awaited()
    trigger_post_call_mock.assert_not_awaited()
    handler.end_call.assert_awaited_once_with("idle_timeout")


@pytest.mark.asyncio
async def test_idle_disconnect_returns_immediately_when_already_shutting_down() -> None:
    lkh = _load_lite_handler_module()
    handler = lkh.LiveKitLiteHandler(session_id="id")
    handler._is_shutting_down = True
    handler.end_call = AsyncMock()

    await handler._handle_idle_disconnect()

    handler.end_call.assert_not_awaited()
