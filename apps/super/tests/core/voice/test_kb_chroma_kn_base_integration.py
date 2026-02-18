import asyncio
import json
import logging
import os
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from tests.core.voice.helpers.runtime_imports import prepare_runtime_imports
from super.core.memory.search.schema import SearchDoc


KN_BASE_TOKENS = ["AA336J3AS6ZINF6L5ESMTLZG"]

QA_CASES = [
    {
        "question": "What is the fees for the two year GS Course , I want to take admission ?",
        "required_keywords": ["2 year", "classroom mode", "2 lakh 45,000"],
    },
    {
        "question": "When is the next batch of sureshot test series for seniors is going to start ?",
        "required_keywords": ["eighteenth january", "seniors"],
    },
    {
        "question": "What is the fees of CSAT course in offline mode?",
        "required_keywords": ["eighteen thousand", "offline mode", "inclusive of gst"],
    },
    {
        "question": "What is the duration of prelims camp 2026 ?",
        "required_keywords": ["thirty first may", "2026"],
    },
    {
        "question": "Why should I join Vajiram and ravi?",
        "required_keywords": ["50 saal", "top results", "complete preparation"],
    },
    {
        "question": "How do I complete the OTR process?",
        "required_keywords": ["one time registration", "documents upload", "otr id"],
    },
    {
        "question": "Which services can I get through this exam?",
        "required_keywords": ["twenty-three services", "ias", "ifs", "ips"],
    },
    {
        "question": "Can you tell me about the batch timings of General Studies Prelims and Mains course in Online mode ?",
        "required_keywords": ["two thirty", "seven thirty", "five thirty"],
    },
    {
        "question": "Can you tell me about the Sure shot PYQ dominator ?",
        "required_keywords": [
            "twenty four pyq-based tests",
            "detailed evaluation within seven working days",
            "mentor support",
        ],
    },
]


def _is_remote_kb_enabled() -> bool:
    return (
        os.getenv("RUN_KB_REMOTE_E2E", "").lower() in {"1", "true", "yes"}
        and bool(os.getenv("SEARCH_SERVICE_URL"))
    )


def _print_docs_for_question(question: str, docs) -> None:
    print("\n[KB-E2E] QUESTION:")
    print(question)
    if not docs:
        print("[KB-E2E] No docs returned")
        return
    for i, doc in enumerate(docs):
        score = getattr(doc, "score", None)
        score_str = f"{score:.4f}" if isinstance(score, (float, int)) else "n/a"
        preview = " ".join(str(getattr(doc, "content", "")).split())[:220]
        doc_id = getattr(doc, "document_id", "unknown")
        print(f"[KB-E2E][{i}] score={score_str} id={doc_id} :: {preview}")


@pytest.fixture(scope="module")
def remote_chroma_kb_manager():
    if not _is_remote_kb_enabled():
        pytest.skip(
            "Set RUN_KB_REMOTE_E2E=1 and SEARCH_SERVICE_URL to run remote KN_BASE tests."
        )

    # For QA evaluation, default to full KN_BASE coverage unless explicitly overridden.
    env_defaults = {
        "KB_MIN_REMOTE_SCORE": "0",
        "KB_MIN_SCORE": "0",
    }
    env_applied = []
    for key, value in env_defaults.items():
        if key not in os.environ:
            os.environ[key] = value
            env_applied.append(key)

    prepare_runtime_imports()
    from super.core.voice.managers.knowledge_base import KnowledgeBaseManager

    manager = KnowledgeBaseManager(
        logger=logging.getLogger("kb_remote_e2e"),
        session_id="kb_remote_e2e_session",
        vector_backend="chroma",
    )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(manager._init_context_retrieval())

    remote_docs = loop.run_until_complete(
        manager._fetch_remote_documents("file", KN_BASE_TOKENS, page_size=300)
    )
    assert remote_docs, "No remote docs fetched for configured KN_BASE token"

    loop.run_until_complete(manager._cache_documents(remote_docs))
    print(
        f"[KB-E2E] indexed_docs={len(remote_docs)} "
        f"kn_base={KN_BASE_TOKENS} "
        f"kb_min_remote_score={os.getenv('KB_MIN_REMOTE_SCORE')} "
        f"kb_min_score={os.getenv('KB_MIN_SCORE')}"
    )

    try:
        yield manager
    finally:
        for key in env_applied:
            os.environ.pop(key, None)


@pytest.mark.integration
@pytest.mark.slow
def test_chroma_answers_for_kn_base_questions(remote_chroma_kb_manager):
    """Load KN_BASE docs, index in Chroma, query each Q&A, and print returned docs."""
    manager = remote_chroma_kb_manager
    loop = asyncio.get_event_loop()
    failures = []

    for case in QA_CASES:
        question = case["question"]
        required_keywords = case["required_keywords"]

        docs = loop.run_until_complete(manager._search_documents(question, k=5))
        _print_docs_for_question(question, docs)

        if not docs:
            failures.append(
                f"Question={question!r} -> no docs returned"
            )
            continue

        combined = " ".join(getattr(d, "content", "") for d in docs).lower()
        missing = [kw for kw in required_keywords if kw.lower() not in combined]
        if missing:
            failures.append(
                f"Question={question!r} -> missing keywords={missing}"
            )

    assert not failures, (
        "Chroma retrieval quality mismatches:\n- "
        + "\n- ".join(failures)
        + "\nSee printed [KB-E2E] docs for each question above."
    )


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_livekit_agent_get_docs_injects_reference_context(remote_chroma_kb_manager):
    """
    Verify LiveKit agent get_docs tool injects retrieved KB context in payload
    consumed by the LLM tool-call path.
    """
    prepare_runtime_imports()
    import super.core.voice.livekit.livekit_lite_agent as lka

    agent = object.__new__(lka.LiveKitLiteAgent)
    agent._kb_tool_calls = 0
    agent._logger = MagicMock()
    agent.config = {}
    agent.user_state = SimpleNamespace(
        knowledge_base=[{"token": KN_BASE_TOKENS[0], "name": "vajiram"}],
        token=None,
    )

    kb_ready = asyncio.Event()
    kb_ready.set()
    agent.handler = SimpleNamespace(
        _kb_manager=remote_chroma_kb_manager,
        _kb_ready=kb_ready,
        _session_id="kb_remote_e2e_session",
    )

    _, payload = await agent.get_docs(
        MagicMock(),
        query="fees for GS course",
        kb_name="",
    )
    data = json.loads(payload)
    print("\n[KB-E2E] LiveKit tool payload:", json.dumps(data, indent=2)[:1200])

    assert "Reference Docs" in data
    assert isinstance(data["Reference Docs"], list)
    assert len(data["Reference Docs"]) > 0

    flattened = json.dumps(data["Reference Docs"]).lower()
    assert any(
        token in flattened for token in ["gs", "fees", "classroom", "2 year"]
    ), "LiveKit payload did not include expected KB context tokens."


@pytest.mark.asyncio
async def test_livekit_agent_injects_reference_docs_payload_unit():
    """Unit guard: LiveKit get_docs tool should inject KB docs in returned payload."""
    prepare_runtime_imports()
    import super.core.voice.livekit.livekit_lite_agent as lka

    class _FakeKBManager:
        async def get_docs(self, **_kwargs):
            return [
                SearchDoc(
                    document_id="unit_doc_1",
                    content="The fees for the 2 year GS course is 2 lakh 45,000 rupees.",
                    blurb="fees answer",
                    source_type="file",
                    semantic_identifier="unit_doc_1",
                    metadata={"source": "unit"},
                    score=0.91,
                )
            ]

    agent = object.__new__(lka.LiveKitLiteAgent)
    agent._kb_tool_calls = 0
    agent._logger = MagicMock()
    agent.config = {}
    agent.user_state = SimpleNamespace(
        knowledge_base=[{"token": "unit-token", "name": "unit-kb"}],
        token=None,
    )

    kb_ready = asyncio.Event()
    kb_ready.set()
    agent.handler = SimpleNamespace(
        _kb_manager=_FakeKBManager(),
        _kb_ready=kb_ready,
        _session_id="unit_session",
    )

    _, payload = await agent.get_docs(
        MagicMock(),
        query="fees for GS course",
        kb_name="",
    )

    data = json.loads(payload)
    assert "Reference Docs" in data
    assert len(data["Reference Docs"]) == 1
    flattened = json.dumps(data["Reference Docs"]).lower()
    assert "2 year gs course" in flattened
    assert "2 lakh 45,000" in flattened
