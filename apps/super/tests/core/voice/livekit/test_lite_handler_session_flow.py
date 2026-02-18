import asyncio
import sys
import types
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


@pytest.mark.asyncio
async def test_background_kb_warmup_sets_ready_before_preload(monkeypatch) -> None:
    lkh = _load_lite_handler_module()
    handler = lkh.LiveKitLiteHandler(session_id="kb-warmup")
    handler.config = {"knowledge_base": [{"token": "kb1"}]}
    handler.user_state = MagicMock(knowledge_base=[{"token": "kb1"}], token="tok")

    events = []

    class FakeKnowledgeBaseManager:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        async def _init_context_retrieval(self):
            events.append(("init", handler._kb_ready.is_set()))

        async def _preload_knowledge_base_documents(self, _user_state):
            # Readiness should already be signaled before potentially long preload.
            events.append(("preload_start", handler._kb_ready.is_set()))
            await asyncio.sleep(0)
            events.append(("preload_end", handler._kb_ready.is_set()))
            return True

    kb_module = types.ModuleType("super.core.voice.managers.knowledge_base")
    kb_module.KnowledgeBaseManager = FakeKnowledgeBaseManager
    monkeypatch.setitem(
        sys.modules,
        "super.core.voice.managers.knowledge_base",
        kb_module,
    )

    await handler._background_kb_warmup(immediate=True)

    assert handler._kb_ready.is_set()
    assert handler._kb_manager is not None
    assert ("preload_start", True) in events
