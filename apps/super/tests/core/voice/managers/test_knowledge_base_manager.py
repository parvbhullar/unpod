import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from tests.core.voice.helpers.runtime_imports import prepare_runtime_imports


def _load_kb_module():
    prepare_runtime_imports()
    import super.core.voice.managers.knowledge_base as kb

    return kb


@pytest.mark.asyncio
async def test_fetch_remote_documents_uses_to_thread(monkeypatch) -> None:
    kb = _load_kb_module()
    manager = kb.KnowledgeBaseManager(logger=MagicMock(), session_id="s1")

    thread_calls = []

    async def fake_to_thread(func, *args, **kwargs):
        thread_calls.append((func, args, kwargs))
        return SimpleNamespace(
            status_code=200,
            json=lambda: {
                "data": {
                    "search_response_summary": {
                        "top_sections": [
                            {
                                "blurb": "b",
                                "content": "shipping help",
                                "source_type": "kb",
                                "document_id": "d1",
                                "semantic_identifier": "sid",
                                "metadata": {},
                                "url": "u",
                                "score": 0.9,
                            }
                        ]
                    }
                }
            },
        )

    monkeypatch.setattr(kb.asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(kb.os, "getenv", lambda key, default=None: "http://svc" if key == "SEARCH_SERVICE_URL" else default)

    docs = await manager._fetch_remote_documents("shipping", ["kb-token"])

    assert len(thread_calls) == 1
    assert len(docs) == 1


@pytest.mark.asyncio
async def test_get_docs_waits_for_preload_before_remote_fallback(monkeypatch) -> None:
    kb = _load_kb_module()
    manager = kb.KnowledgeBaseManager(logger=MagicMock(), session_id="s2")

    user_state = SimpleNamespace(
        knowledge_base=[{"token": "kb-token"}],
        token=None,
    )

    # Simulate preload in progress that finishes quickly.
    manager._preload_in_progress = True
    manager._preload_complete.clear()

    search_calls = {"count": 0}
    remote_calls = {"count": 0}

    async def fake_search(_query: str, k: int = 3):
        search_calls["count"] += 1
        if search_calls["count"] == 1:
            return []
        return [SimpleNamespace(content="shipping policy")]

    async def fake_remote(*args, **kwargs):
        remote_calls["count"] += 1
        return []

    async def release_preload():
        await asyncio.sleep(0)
        manager._preload_in_progress = False
        manager._preload_complete.set()

    monkeypatch.setattr(manager, "_search_documents", fake_search)
    monkeypatch.setattr(manager, "_fetch_remote_documents", fake_remote)
    asyncio.create_task(release_preload())

    docs = await manager.get_docs(query="shipping", user_state=user_state)

    assert remote_calls["count"] == 0
    assert len(docs) == 1


@pytest.mark.asyncio
async def test_fetch_remote_documents_file_query_bypasses_score_filter(monkeypatch) -> None:
    kb = _load_kb_module()
    manager = kb.KnowledgeBaseManager(logger=MagicMock(), session_id="s3")

    async def fake_to_thread(func, *args, **kwargs):
        return SimpleNamespace(
            status_code=200,
            json=lambda: {
                "data": {
                    "search_response_summary": {
                        "top_sections": [
                            {
                                "blurb": "high-score",
                                "content": "general studies two year course fees",
                                "source_type": "kb",
                                "document_id": "d_high",
                                "semantic_identifier": "sid-high",
                                "metadata": {},
                                "url": "u1",
                                "score": 0.92,
                            },
                            {
                                "blurb": "low-score",
                                "content": "exact fee is two lakh forty five thousand",
                                "source_type": "kb",
                                "document_id": "d_low",
                                "semantic_identifier": "sid-low",
                                "metadata": {},
                                "url": "u2",
                                "score": 0.12,
                            },
                        ]
                    }
                }
            },
        )

    def fake_getenv(key, default=None):
        if key == "SEARCH_SERVICE_URL":
            return "http://svc"
        if key == "KB_MIN_REMOTE_SCORE":
            return "0.50"
        return default

    monkeypatch.setattr(kb.asyncio, "to_thread", fake_to_thread)
    monkeypatch.setattr(kb.os, "getenv", fake_getenv)

    docs = await manager._fetch_remote_documents("file", ["kb-token"])
    doc_ids = [doc.document_id for doc in docs]

    assert doc_ids == ["d_high", "d_low"]
