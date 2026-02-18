import asyncio
import uuid

from super.core.memory.index.chroma import ChromaIndex
from super.core.memory.search.schema import SearchDoc


def _make_doc(doc_id: str, content: str) -> SearchDoc:
    return SearchDoc(
        document_id=doc_id,
        content=content,
        blurb=content[:80],
        source_type="file",
        semantic_identifier=doc_id,
        metadata={"source": "fetch_k_test"},
    )


def _build_index() -> ChromaIndex:
    idx = ChromaIndex(index_name=f"fetch_k_test_{uuid.uuid4().hex[:8]}")
    docs = [
        _make_doc("d1", "Vajiram and Ravi GS fees and classroom details"),
        _make_doc("d2", "OTR process and registration details"),
        _make_doc("d3", "UPSC services list includes IAS and IPS"),
        _make_doc("d4", "Hostel and library facilities near campus"),
        _make_doc("d5", "Batch timings and schedule for GS course"),
        _make_doc("d6", "Sure shot PYQ dominator test programme"),
    ]
    asyncio.get_event_loop().run_until_complete(idx.index(docs))
    return idx


def test_search_sync_fetch_k_expands_candidate_pool() -> None:
    idx = _build_index()

    baseline = idx.search_sync("vajiram course details", k=2)
    expanded = idx.search_sync("vajiram course details", k=2, fetch_k=5)

    assert len(baseline) == 2
    assert len(expanded) == 5


def test_search_sync_fetch_k_never_reduces_below_k() -> None:
    idx = _build_index()

    results = idx.search_sync("upsc services", k=3, fetch_k=1)

    assert len(results) == 3


def test_async_search_fetch_k_expands_candidate_pool() -> None:
    idx = _build_index()

    results = asyncio.get_event_loop().run_until_complete(
        idx.search("upsc and vajiram", k=2, fetch_k=4)
    )

    assert len(results) == 4


def test_index_preserves_distinct_sections_for_duplicate_doc_ids() -> None:
    idx = ChromaIndex(index_name=f"dup_sections_{uuid.uuid4().hex[:8]}")
    docs = [
        _make_doc("shared_doc", "Fees for GS course in classroom mode"),
        _make_doc("shared_doc", "OTR process steps and registration details"),
    ]

    asyncio.get_event_loop().run_until_complete(idx.index(docs))

    assert idx.document_count == 2

    results = idx.search_sync("fees and otr details", k=5, fetch_k=5)
    contents = " ".join(r.content.lower() for r in results)
    ids = {r.document_id for r in results}

    assert "fees for gs course" in contents
    assert "otr process steps" in contents
    assert len(ids) == 2
