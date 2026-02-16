import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.core.voice.helpers.runtime_imports import prepare_runtime_imports


def _load_voice_agent_handler_module():
    prepare_runtime_imports()
    import super.core.voice.voice_agent_handler as vah

    return vah


@pytest.mark.asyncio
async def test_start_recording_background_timeout_does_not_raise() -> None:
    vah = _load_voice_agent_handler_module()
    handler = vah.VoiceAgentHandler(session_id="t-4")
    handler.start_session_recording = AsyncMock(side_effect=asyncio.TimeoutError)

    ctx = MagicMock(room=MagicMock(name="room-x"))
    user_state = MagicMock(recording_url="")

    await handler._start_recording_background(ctx, user_state, "s1")

    assert user_state.recording_url == ""


@pytest.mark.asyncio
async def test_publish_transcript_returns_false_without_bridge() -> None:
    vah = _load_voice_agent_handler_module()
    handler = vah.VoiceAgentHandler(session_id="t-5")

    ok = await handler.publish_transcript(role="assistant", content="hi", is_final=True)

    assert ok is False


@pytest.mark.asyncio
async def test_publish_data_returns_strict_bool() -> None:
    vah = _load_voice_agent_handler_module()
    handler = vah.VoiceAgentHandler(session_id="t-6")
    handler._event_bridge = MagicMock(publish_data=AsyncMock(return_value={"ok": 1}))

    result = await handler.publish_data({"msg": "hello"})

    assert isinstance(result, bool)
    assert result is True


@pytest.mark.asyncio
async def test_publish_message_callback_returns_strict_bool() -> None:
    vah = _load_voice_agent_handler_module()
    handler = vah.VoiceAgentHandler(session_id="t-7")
    handler._event_bridge = MagicMock(
        publish_message_callback=AsyncMock(return_value="published")
    )

    result = await handler.publish_message_callback({"content": "hello"})

    assert isinstance(result, bool)
    assert result is True
