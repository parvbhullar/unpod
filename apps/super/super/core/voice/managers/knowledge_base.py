"""
Knowledge Base Manager for Pipecat Voice Handler

This module provides a standalone class for managing knowledge base operations,
supporting both FAISS and ChromaDB backends for context retrieval, document caching,
and remote search fallback.

Environment Variables:
    VECTOR_BACKEND: 'faiss' or 'chroma' (default: 'faiss')
    INMEMORY_KB_PAGE_SIZE: Number of documents to retrieve (default: 3)
    CHROMA_PERSIST_DIR: Directory for ChromaDB persistence (optional)
"""

import asyncio
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional, Union

import requests

from super.core.memory.index.base import BaseIndex
from super.core.memory.index.factory import VectorBackend, create_vector_index
from super.core.memory.search.schema import SearchDoc
from pipecat.services.llm_service import FunctionCallParams
from super.core.voice.schema import UserState


# Domain abbreviation → expansion mappings for query enrichment.
# Each key is matched case-insensitively as a whole word; the expansion is
# appended to the query so that the vector search can find documents using
# either the abbreviation or the full phrase.
_DOMAIN_SYNONYMS: Dict[str, str] = {
    "pyq": "previous year question",
    "gs": "general studies",
    "otr": "one time registration",
    "csat": "civil services aptitude test",
    "ias": "indian administrative service",
    "ifs": "indian foreign service",
    "ips": "indian police service",
    "upsc": "union public service commission",
    "sip": "systematic investment plan",
}


def _expand_query(query: str) -> str:
    """Expand domain abbreviations in *query* for better vector recall."""
    query_lower = query.lower()
    expansions: List[str] = []
    for abbr, full in _DOMAIN_SYNONYMS.items():
        # Whole-word match to avoid false positives (e.g. "gas" containing "gs")
        if re.search(rf"\b{re.escape(abbr)}\b", query_lower):
            expansions.append(full)
    if expansions:
        return f"{query} ({' '.join(expansions)})"
    return query


class KnowledgeBaseManager:
    """
    Manages knowledge base operations with pluggable vector backends.

    Supports both FAISS and ChromaDB backends, switchable via VECTOR_BACKEND env var.
    ChromaDB provides lower-latency synchronous search for real-time RAG in voice pipelines.
    """

    def __init__(
        self,
        logger: logging.Logger,
        session_id: Optional[str] = None,
        user_state: Optional[UserState] = None,
        config: Optional[Dict[str, Any]] = None,
        vector_backend: Optional[Union[VectorBackend, str]] = None,
    ):
        """
        Initialize the Knowledge Base Manager.

        Args:
            logger: Logger instance for logging operations
            session_id: Optional session identifier
            user_state: Optional user state containing knowledge base configurations
            config: Optional configuration dict (for refresh_index setting)
            vector_backend: Vector backend to use ('faiss' or 'chroma').
                           If None, reads from VECTOR_BACKEND env var (default: 'faiss')
        """
        self._logger = logger
        self._session_id = session_id
        self.user_state = user_state
        self.config = config or {}
        self._memory_index: Optional[BaseIndex] = None
        self._index_name = self.index_name(session_id, user_state)
        self.kb_page_size = int(os.getenv("INMEMORY_KB_PAGE_SIZE", 5))
        self._refresh_index = self.config.get("refresh_index", False)
        self._preload_in_progress: bool = False
        self._preload_complete: asyncio.Event = asyncio.Event()
        self._preload_complete.set()

        # Determine vector backend
        if vector_backend is not None:
            if isinstance(vector_backend, str):
                try:
                    self._vector_backend = VectorBackend(vector_backend.lower())
                except ValueError:
                    self._logger.warning(
                        f"Invalid vector_backend '{vector_backend}', using faiss"
                    )
                    self._vector_backend = VectorBackend.FAISS
            else:
                self._vector_backend = vector_backend
        else:
            backend_str = os.getenv("VECTOR_BACKEND", "faiss").lower()
            try:
                self._vector_backend = VectorBackend(backend_str)
            except ValueError:
                self._vector_backend = VectorBackend.FAISS

        self._logger.info(f"KnowledgeBaseManager using backend: {self._vector_backend.value}")

    @staticmethod
    def index_name(session_id, user_state):
        return "_".join([kn.get("token") for kn in
                         user_state.knowledge_base]) if user_state and user_state.knowledge_base else session_id

    async def _init_context_retrieval(self) -> None:
        """
        Initialize the context retrieval system with configured vector backend.

        Uses refresh_index config to determine if existing index should be reused:
        - refresh_index=False (default): Reuse index if < 24 hours old
        - refresh_index=True: Always create fresh index

        Backend is determined by:
        1. vector_backend constructor argument
        2. VECTOR_BACKEND environment variable
        3. Default: 'faiss'
        """
        if self._memory_index is None:
            try:
                self._memory_index = create_vector_index(
                    index_name=self._index_name,
                    backend=self._vector_backend,
                    refresh_index=self._refresh_index,
                )
                self._logger.info(
                    f"Initialized context retrieval with {self._vector_backend.value.upper()} "
                    f"(refresh_index={self._refresh_index}, index_name={self._index_name})"
                )
            except Exception as e:
                self._logger.error(f"Error initializing context retrieval: {e}")
                raise

    async def _search_documents(self, query: str, k: int = 3) -> List[SearchDoc]:
        """
        Search for documents using configured vector backend.

        Args:
            query: Search query string
            k: Number of top results to return

        Returns:
            List of SearchDoc objects
        """
        if not self._memory_index:
            await self._init_context_retrieval()

        try:
            # Expand domain abbreviations for better vector recall
            expanded_query = _expand_query(query)

            # Retrieve a wider candidate pool for reranking when enabled.
            use_reranker = os.getenv("KB_USE_RERANKER", "true").lower() == "true"
            fetch_k = k
            if use_reranker:
                try:
                    multiplier = int(os.getenv("KB_FETCH_K_MULTIPLIER", "3"))
                except ValueError:
                    multiplier = 3
                fetch_k = max(k, k * max(1, multiplier))

            results = await self._memory_index.search(
                expanded_query, k=k, fetch_k=fetch_k
            )

            # Filter by minimum score threshold
            min_score = float(os.getenv("KB_MIN_SCORE", 0.30))
            if min_score > 0 and results:
                pre_filter_count = len(results)
                results = [r for r in results if r.score >= min_score]
                if len(results) < pre_filter_count:
                    self._logger.debug(
                        f"KB score filter: {pre_filter_count} -> {len(results)} "
                        f"(min_score={min_score})"
                    )

            # Hybrid reranking (dense + lexical + intent)
            if use_reranker and results:
                from super.core.memory.search.reranker import hybrid_rerank

                results = hybrid_rerank(query, results)

            # Keep API contract: _search_documents(query, k) returns at most k docs.
            if len(results) > k:
                results = results[:k]

            if results:
                score_range = f"[{results[-1].score:.4f}..{results[0].score:.4f}]"
                self._logger.debug(
                    f"KB search: query={query!r}, k={k}, found={len(results)}, "
                    f"scores={score_range}, top_ids={[r.document_id for r in results[:3]]}"
                )
            self._logger.info(f"Found {len(results)} documents for query")
            return results
        except Exception as e:
            self._logger.error(f"Search failed: {e}")
            return []

    def search_documents_sync(self, query: str, k: int = 3) -> List[SearchDoc]:
        """
        Synchronous search for documents (for use in frame processors).

        Only available with ChromaDB backend. Falls back to empty list for FAISS.

        Args:
            query: Search query string
            k: Number of top results to return

        Returns:
            List of SearchDoc objects
        """
        if not self._memory_index:
            self._logger.warning("Index not initialized for sync search")
            return []

        # Check if backend supports sync search (ChromaDB)
        if hasattr(self._memory_index, "search_sync"):
            try:
                return self._memory_index.search_sync(query, k=k)
            except Exception as e:
                self._logger.error(f"Sync search failed: {e}")
                return []

        self._logger.debug("Sync search not available for this backend")
        return []

    async def build_context_message(self, transcript_text: str) -> Optional[str]:
        """
        Build a formatted context message by fetching relevant knowledge base documents.

        Args:
            transcript_text: Transcript text to search against

        Returns:
            Context message string or None if no relevant documents were found
        """
        start_time = time.time()
        docs = await self._search_documents(transcript_text, k=self.kb_page_size)
        if not docs:
            return None

        try:
            context_str = "\n- " + "\n- ".join(doc.content for doc in docs)
            message = f"[Important Context]:{context_str}"
            elapsed_ms = (time.time() - start_time) * 1000
            self._logger.info(
                "Built KB context message with %d docs in %.1fms",
                len(docs),
                elapsed_ms,
            )
            return message
        except Exception as exc:
            self._logger.error("Error formatting context message: %s", exc)
            return None

    async def _add_faiss_context_to_transcript(self, transcript_text: str) -> str:
        """
        Add FAISS context to transcript text before sending to LLM.

        Args:
            transcript_text: The transcript text to enhance with context

        Returns:
            Enhanced transcript text with FAISS context
        """
        if not transcript_text or not isinstance(transcript_text, str):
            self._logger.warning("Invalid transcript text provided")
            return transcript_text

        transcript_text = transcript_text.strip()
        if len(transcript_text) < 3:
            self._logger.debug("Transcript text too short for context search")
            return transcript_text

        if not self._memory_index:
            self._logger.debug("Context retrieval components not initialized")
            return transcript_text

        try:
            context_message = await self.build_context_message(transcript_text)
            if context_message:
                return f"""{context_message}

                    [USER QUERY]
                    {transcript_text}"""
            return transcript_text
        except Exception as exc:
            self._logger.error(
                "Unexpected error in _add_faiss_context_to_transcript: %s",
                exc,
                exc_info=self._logger.isEnabledFor(logging.DEBUG),
            )
            return transcript_text

    async def _cache_documents(self, search_docs: List[SearchDoc]) -> None:
        """
        Cache documents in the vector index.

        Args:
            search_docs: List of SearchDoc objects to cache
        """
        if not search_docs or not self._memory_index:
            return

        try:
            await self._memory_index.index(search_docs, deep_chunking=False)
            self._logger.info(
                f"Cached {len(search_docs)} documents in {self._vector_backend.value.upper()} index"
            )
        except Exception as e:
            self._logger.error(f"Failed to cache documents: {e}")

    async def _fetch_remote_documents(
        self, query: str, kn_bases: List[str], page_size: Optional[int] = None
    ) -> List[SearchDoc]:
        """
        Fetch documents from remote search service with retry mechanism.

        Args:
            query: Search query string
            kn_bases: List of knowledge base tokens

        Returns:
            List of SearchDoc objects from remote search
        """
        url_base = os.getenv("SEARCH_SERVICE_URL", "").rstrip("/")
        if not url_base:
            self._logger.error("SEARCH_SERVICE_URL not set")
            return []

        url = f"{url_base}/api/v1/search/query/docs/"
        payload = {"query": query, "kn_token": kn_bases}
        max_retries = 3
        retry_delay = 0.5  # Initial delay in seconds

        for attempt in range(1, max_retries + 1):
            try:
                try:
                    resolved_page_size = page_size or int(
                        os.getenv("REMOTE_KB_PAGE_SIZE", 200)
                    )
                except ValueError:
                    resolved_page_size = 200
                params = {"page_size": resolved_page_size}
                self._logger.info(f"Fetching remote documents (attempt {attempt}/{max_retries})")
                response = await asyncio.to_thread(
                    requests.post,
                    url,
                    json=payload,
                    params=params,
                    timeout=20,
                )

                if response.status_code == 200:
                    result = response.json()

                    # self._logger.info(f"Fetched {result} documents in FAISS index \n\n\n {payload}")
                    docs = result.get("data", {}).get("search_response_summary", {}).get("top_sections", [])

                    is_corpus_fetch = query.strip().lower() == "file"
                    if is_corpus_fetch:
                        # Preload/index build should maximize KB coverage.
                        # Remote search scores for synthetic "file" query are noisy and
                        # can drop critical sections needed for later local retrieval.
                        filtered_docs = [
                            doc for doc in docs if len(doc.get("content", "")) > 0
                        ]
                        self._logger.debug(
                            f"Remote corpus fetch bypassed score filter: "
                            f"{len(docs)} -> {len(filtered_docs)} (query='file')"
                        )
                    else:
                        self._logger.info("Fetched documents, applying score filter")
                        min_remote_score = float(os.getenv("KB_MIN_REMOTE_SCORE", 0.50))
                        filtered_docs = [
                            doc
                            for doc in docs
                            if (
                                doc.get("score", 0) >= min_remote_score
                                and len(doc.get("content", "")) > 0
                            )
                        ]
                        self._logger.debug(
                            f"Remote score filter: {len(docs)} -> {len(filtered_docs)} "
                            f"(min_score={min_remote_score})"
                        )

                    search_docs = [SearchDoc.from_dict(doc) for doc in (filtered_docs or docs)]
                    self._logger.info(f"Fetched {len(search_docs)} documents from remote service")
                    return search_docs
                else:
                    self._logger.warning(
                        f"Remote search failed with status {response.status_code} (attempt {attempt}/{max_retries})"
                    )
                    if attempt < max_retries:
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff

            except Exception as e:
                self._logger.warning(
                    f"Error fetching remote documents (attempt {attempt}/{max_retries}): {e}"
                )
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    self._logger.error(f"Failed to fetch remote documents after {max_retries} attempts")

        return []

    async def _preload_knowledge_base_documents(self, user_state: Optional[UserState] = None) -> bool:
        """
        Pre-load knowledge base documents into the local FAISS index.

        Respects refresh_index configuration:
        - refresh_index=False (default): Skip preload if index < 24 hours old
        - refresh_index=True: Always fetch and preload documents

        Args:
            user_state: Optional user state containing knowledge base configurations

        Returns:
            True if successful or no documents to load, False on error
        """
        if user_state is None:
            user_state = self.user_state

        if user_state is None:
            self._logger.warning("No user state available for preloading documents")
            return False

        self._preload_in_progress = True
        self._preload_complete.clear()

        try:
            await self._init_context_retrieval()
        except Exception as e:
            self._logger.error(f"Init context retrieval failed before preload: {e}")
            self._preload_in_progress = False
            self._preload_complete.set()
            return False

        # ✅ FIXED: Check if index should be refreshed before fetching documents
        if not self._memory_index.should_refresh_index():
            self._logger.info("Skipping document preload - using existing index (< 24h old)")
            return True

        preload_start = time.time()

        try:
            # Get all knowledge bases from user_state
            kn_list = getattr(user_state, 'knowledge_base', [])

            if not kn_list:
                self._logger.info("No knowledge bases found, skipping document preload")
                return True

            # Collect and deduplicate knowledge base tokens
            kn_bases = list(dict.fromkeys(
                item.get("token") for item in kn_list if item.get("token")
            ))

            if not kn_bases:
                self._logger.info("No valid knowledge base tokens found, skipping document preload")
                return True

            self._logger.info(f"Pre-loading documents from {len(kn_bases)} knowledge bases: {kn_bases}")
            print(f"Pre-loading documents from {len(kn_bases)} knowledge bases: {kn_bases}")

            # Fetch documents from remote service
            remote_docs = await self._fetch_remote_documents("file", kn_bases)
            if remote_docs:
                await self._cache_documents(remote_docs)
                preload_time = (time.time() - preload_start) * 1000
                self._logger.info(f"Successfully pre-loaded {len(remote_docs)} documents in {preload_time:.2f}ms")
            else:
                self._logger.warning("No documents were pre-loaded")

            return True

        except Exception as e:
            self._logger.error(f"Error in document pre-loading: {e}")
            return False
        finally:
            self._preload_in_progress = False
            self._preload_complete.set()

    async def _cache_transcript_entry(self, transcript_entry: Dict[str, Any]) -> None:
        """
        Cache transcript entry in FAISS for conversation memory.

        Args:
            transcript_entry: Dictionary containing transcript entry with content and metadata
        """
        if not self._memory_index:
            return

        try:
            content = transcript_entry.get("content", "")
            if not content or len(content.strip()) < 5:  # Only cache meaningful content
                return

            # Create SearchDoc for caching with conversation metadata
            search_doc = SearchDoc(
                blurb=f"{transcript_entry.get('role', 'unknown')}: {content[:100]}",
                content=content,
                source_type="conversation_transcript",
                document_id=f"transcript_{self._session_id}_{int(time.time() * 1000)}",
                semantic_identifier=f"conversation_{transcript_entry.get('role', 'unknown')}",
                metadata={
                    "source": "conversation_transcript",
                    "role": transcript_entry.get("role", "unknown"),
                    "user_id": transcript_entry.get("user_id", "unknown"),
                    "timestamp": transcript_entry.get("timestamp", ""),
                    "session_id": self._session_id or 'unknown'
                },
                url=f"conversation://{self._session_id}",
                score=0.9  # High score for recent conversation content
            )

            await self._cache_documents([search_doc])
            self._logger.info(
                f"Cached transcript entry: {len(content)} chars, role: {transcript_entry.get('role')}")

        except Exception as e:
            self._logger.error(f"Error caching transcript entry: {e}")

    async def get_docs(
        self,
        params: Optional[FunctionCallParams] = None,
        query: Optional[str] = None,
        kn_name: Optional[str] = None,
        user_state: Optional[UserState] = None
    ) -> List[SearchDoc]:
        """
        Get relevant documents from the knowledge base.

        This tool is called when the user asks a query or information.
        This function will return the relevant documents to answer the user.
        Fallback to this function if not able to answer the question.

        Args:
            params: Optional FunctionCallParams object
            query: Search query (can be provided directly or via params.arguments)
            kn_name: Optional knowledge base name filter
            user_state: Optional user state, uses instance user_state if not provided

        Returns:
            Dictionary containing relevant documents or error information
        """
        # Use provided user_state or fall back to instance user_state
        user_state = user_state or self.user_state

        if user_state is None:
            return {"error": "No user state available"}

        # Extract arguments from params if provided
        arguments = getattr(params, 'arguments', {}) if params else {}

        # Get query and kn_name from parameters or direct arguments
        query = query or arguments.get("query", "")
        kn_name = kn_name or arguments.get("kn_name")

        if not query:
            return {"error": "No query provided"}

        try:
            # Get knowledge base tokens
            kn_list = getattr(user_state, 'knowledge_base', [])
            token = getattr(user_state, 'token', None)

            # Filter by kn_name if provided, otherwise use all
            if kn_name:
                kn_bases = [item["token"] for item in kn_list if item.get("name") == kn_name]
            else:
                kn_bases = [item["token"] for item in kn_list if item.get("token")]

            # Add user's token if available
            if not kn_bases:
                kn_bases = [item["token"] for item in kn_list if item.get("token")]

            if token:
                kn_bases.append(token)


            if not kn_bases:
                kn_bases=[item["token"] for item in kn_list if item.get("token")]

                if not  kn_bases:
                    return {"error": "No knowledge base available"}

            self._logger.info(f"Searching for documents with query: {query}")

            # Search local index first
            docs = await self._search_documents(query, k=self.kb_page_size)

            # Fallback to remote if no local results
            if not docs and kn_bases:
                remote_docs: List[SearchDoc] = []
                if self._preload_in_progress:
                    wait_sec = float(os.getenv("KB_PRELOAD_WAIT_ON_QUERY_SEC", "1.5"))
                    self._logger.info(
                        f"KB preload in progress, waiting up to {wait_sec:.1f}s before remote fallback"
                    )
                    try:
                        await asyncio.wait_for(self._preload_complete.wait(), timeout=wait_sec)
                        docs = await self._search_documents(query, k=self.kb_page_size)
                    except asyncio.TimeoutError:
                        self._logger.info(
                            "KB preload still running after wait window; continuing with remote fallback"
                        )

                if not docs:
                    self._logger.info("No local results, fetching from remote service")
                    try:
                        remote_page_size = int(os.getenv("REMOTE_KB_QUERY_PAGE_SIZE", "50"))
                    except ValueError:
                        remote_page_size = 50
                    remote_docs = await self._fetch_remote_documents(
                        query, kn_bases, page_size=remote_page_size
                    )
                    if remote_docs:
                        # Cache remote docs in local index, then re-search
                        # so reranker + score filtering apply uniformly
                        await self._cache_documents(remote_docs)
                        docs = await self._search_documents(
                            query, k=self.kb_page_size
                        )
                        if not docs:
                            # Fallback: use raw remote docs if re-search yields nothing
                            docs = remote_docs

            # Format response
            kb_max_return = int(os.getenv("KB_MAX_RETURN_DOCS", 3))
            result = docs[:kb_max_return]
            score_values: List[str] = []
            for doc in result:
                score = getattr(doc, "score", None)
                if isinstance(score, (int, float)):
                    score_values.append(f"{score:.4f}")
                else:
                    score_values.append("n/a")
            self._logger.debug(
                f"get_docs returning {len(result)} docs for query={query!r}, "
                f"scores={score_values}"
            )

            # Call callback if provided
            if params and hasattr(params, 'result_callback') and callable(params.result_callback):
                self._logger.info("Updating Chat Context with Docs")
                return await params.result_callback(result)

            return result

        except Exception as e:
            self._logger.error(f"Error in get_docs: {e}")
            return {
                "error": str(e),
                "message": "Because of some internal error we are unable to get your relevant information, Please forgive us",
            }

    @property
    def context_retrieval(self) -> Optional[BaseIndex]:
        """Get the context retrieval system (vector index instance)."""
        return self._memory_index

    @property
    def is_initialized(self) -> bool:
        """Check if the knowledge base manager is initialized."""
        return self._memory_index is not None

    @property
    def vector_backend(self) -> VectorBackend:
        """Get the configured vector backend."""
        return self._vector_backend

    @property
    def supports_sync_search(self) -> bool:
        """Check if the current backend supports synchronous search."""
        return (
            self._memory_index is not None
            and hasattr(self._memory_index, "search_sync")
        )

    async def eval_search(
        self,
        query: str,
        expected_doc_id: str,
        k: int = 5,
    ) -> Dict[str, Any]:
        """
        Evaluate search quality for a single query against an expected document.

        Searches the local index and returns rank, score, and hit/miss for the
        expected document. Useful for programmatic evaluation of KB quality.

        Args:
            query: User question to search for
            expected_doc_id: The document_id that should appear in results
            k: Number of results to retrieve

        Returns:
            Dict with keys: query, expected_doc_id, rank (1-based, 0=miss),
            score (float or None), hit (bool), total_results
        """
        docs = await self._search_documents(query, k=k)

        rank = 0
        score = None
        for i, doc in enumerate(docs):
            if doc.document_id == expected_doc_id:
                rank = i + 1
                score = doc.score
                break

        return {
            "query": query,
            "expected_doc_id": expected_doc_id,
            "rank": rank,
            "score": score,
            "hit": rank > 0,
            "total_results": len(docs),
        }

    async def eval_search_batch(
        self,
        test_cases: List[Dict[str, str]],
        k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Evaluate search quality for multiple query/expected_doc_id pairs.

        Args:
            test_cases: List of dicts with 'query' and 'expected_doc_id' keys
            k: Number of results to retrieve per query

        Returns:
            List of eval_search results, one per test case
        """
        results = []
        for case in test_cases:
            result = await self.eval_search(
                query=case["query"],
                expected_doc_id=case["expected_doc_id"],
                k=k,
            )
            results.append(result)
        return results
