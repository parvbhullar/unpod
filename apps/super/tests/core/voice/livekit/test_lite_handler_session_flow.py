from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.core.voice.helpers.runtime_imports import prepare_runtime_imports


def _load_lite_handler_module():
    prepare_runtime_imports(lite_handler_safe=True)
    import super.core.voice.livekit.lite_handler as lkh

    return lkh


@pytest.mark.asyncio
async def test_connect_room_if_needed_skips_when_already_connected() -> None:
    lkh = _load_lite_handler_module()
    handler = lkh.LiveKitLiteHandler(session_id="s")

    ctx = MagicMock(room=MagicMock(connection_state=1), connect=AsyncMock())

    did_connect = await handler._connect_room_if_needed(ctx)

    assert did_connect is False
    ctx.connect.assert_not_awaited()


@pytest.mark.asyncio
async def test_connect_room_if_needed_connects_when_disconnected() -> None:
    lkh = _load_lite_handler_module()
    handler = lkh.LiveKitLiteHandler(session_id="s")

    ctx = MagicMock(room=MagicMock(connection_state=0), connect=AsyncMock())

    did_connect = await handler._connect_room_if_needed(ctx)

    assert did_connect is True
    ctx.connect.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_agent_session_uses_text_mode_factory() -> None:
    lkh = _load_lite_handler_module()
    handler = lkh.LiveKitLiteHandler(session_id="s")
    handler.user_state = MagicMock(
        token="tok",
        knowledge_base=[],
        modality=lkh.Modality.TEXT,
    )

    fake_factory = MagicMock(create_text_session=AsyncMock(return_value="text_session"))
    handler._service_factory = fake_factory

    session = await handler.create_agent_session(MagicMock(room=MagicMock()))

    assert session == "text_session"
    fake_factory.create_text_session.assert_awaited_once()
