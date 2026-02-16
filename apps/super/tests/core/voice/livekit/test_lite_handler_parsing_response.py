from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.core.voice.helpers.runtime_imports import prepare_runtime_imports


def _load_lite_handler_module():
    prepare_runtime_imports(lite_handler_safe=True)
    import super.core.voice.livekit.lite_handler as lkh

    return lkh


def test_parse_block_message_extracts_content_and_files() -> None:
    lkh = _load_lite_handler_module()
    handler = lkh.LiveKitLiteHandler(session_id="x")
    raw = (
        '{"event":"block","data":{"data":{"content":"hello",'
        '"files":[{"name":"a.csv"}]}}}'
    )

    content, block_data, files = handler._parse_block_message(raw)

    assert content == "hello"
    assert block_data["event"] == "block"
    assert len(files) == 1


def test_parse_block_message_handles_null_data_gracefully() -> None:
    lkh = _load_lite_handler_module()
    handler = lkh.LiveKitLiteHandler(session_id="x")
    raw = '{"event":"block","data":null}'

    content, block_data, files = handler._parse_block_message(raw)

    assert content == raw
    assert block_data is None
    assert files is None


@pytest.mark.asyncio
async def test_send_data_response_uses_event_bridge() -> None:
    lkh = _load_lite_handler_module()
    handler = lkh.LiveKitLiteHandler(session_id="x")
    handler.user_state = MagicMock(thread_id="tid", transcript=[], extra_data={})
    handler.agent = MagicMock()
    handler.plugins = MagicMock(broadcast_event=AsyncMock())
    handler._event_bridge = MagicMock(publish_data=AsyncMock(return_value=True))

    await handler._send_data_response("ok")

    handler._event_bridge.publish_data.assert_awaited_once()
    assert handler.user_state.transcript
