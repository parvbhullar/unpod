"""
ChromaDB-based vector index implementation.

Provides synchronous, low-latency vector search using ChromaDB's EphemeralClient
for in-memory operations, optimized for real-time voice pipeline RAG.

Supports multiple embedding backends:
- sentence-transformers: Default PyTorch backend (~20-50ms per embedding)
- openvino: Intel-optimized, 2-4x faster on CPU (~5-15ms per embedding)
- onnx: Portable, ~1.5-2x faster (~10-25ms per embedding)
"""

import os
import re
import time
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Union

from super.core.memory.index.base import BaseIndex
from super.core.memory.search.schema import SearchDoc
from super.core.utils.logger import setup_logger

if TYPE_CHECKING:
    from super.core.memory.index.factory import EmbeddingBackend

logger = setup_logger()


class OpenVINOEmbeddingFunction:
    """
    OpenVINO-optimized embedding function for ChromaDB.

    Uses llama-index's OpenVINOEmbedding for 2-4x faster inference on Intel CPUs.
    Falls back to sentence-transformers if OpenVINO is unavailable.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model_name = model_name
        self._model = None
        self._initialize_model()

    def _initialize_model(self) -> None:
        """Initialize the OpenVINO embedding model."""
        try:
            from llama_index.embeddings.huggingface_openvino import OpenVINOEmbedding

            # OpenVINO expects full model path
            model_id = f"sentence-transformers/{self._model_name}"
            self._model = OpenVINOEmbedding(
                model_id_or_path=model_id,
                device="cpu",
            )
            logger.info(f"OpenVINO embedding initialized: {model_id}")
        except ImportError:
            logger.warning(
                "llama-index-embeddings-huggingface-openvino not installed. "
                "Install with: pip install llama-index-embeddings-huggingface-openvino"
            )
            raise
        except Exception as e:
            logger.error(f"Failed to initialize OpenVINO embedding: {e}")
            raise

    def __call__(self, input: List[str]) -> List[List[float]]:
        """Embed a list of texts using OpenVINO."""
        if not self._model:
            raise RuntimeError("OpenVINO embedding model not initialized")

        embeddings = []
        for text in input:
            embedding = self._model.get_text_embedding(text)
            embeddings.append(embedding)
        return embeddings


class ONNXEmbeddingFunction:
    """
    ONNX-optimized embedding function for ChromaDB.

    Uses ChromaDB's built-in ONNX support for ~1.5-2x faster inference.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model_name = model_name
        self._embedding_fn = None
        self._initialize_model()

    def _initialize_model(self) -> None:
        """Initialize the ONNX embedding function."""
        try:
            from chromadb.utils import embedding_functions

            # ChromaDB has built-in ONNX support for MiniLM
            if "minilm" in self._model_name.lower():
                self._embedding_fn = embedding_functions.ONNXMiniLM_L6_V2()
                logger.info("ONNX MiniLM-L6-v2 embedding initialized (built-in)")
            else:
                # Fall back to sentence-transformers for other models
                logger.warning(
                    f"ONNX not available for {self._model_name}, "
                    "using sentence-transformers"
                )
                self._embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=self._model_name
                )
        except Exception as e:
            logger.error(f"Failed to initialize ONNX embedding: {e}")
            raise

    def __call__(self, input: List[str]) -> List[List[float]]:
        """Embed a list of texts using ONNX."""
        if not self._embedding_fn:
            raise RuntimeError("ONNX embedding function not initialized")
        return self._embedding_fn(input)


class ChromaIndex(BaseIndex):
    """ChromaDB-based vector index implementation optimized for low-latency RAG."""

    def __init__(
        self,
        index_name: str = "default",
        persist_directory: Optional[str] = None,
        embedding_model_name: str = "all-MiniLM-L6-v2",
        embedding_backend: Optional[Union["EmbeddingBackend", str]] = None,
        preloaded_embedding_fn: Optional[Callable] = None,
        preloaded_chroma_client: Optional[Any] = None,
    ):
        """
        Initialize ChromaDB index.

        Args:
            index_name: Name for the collection (uses timestamp if not provided)
            persist_directory: Optional directory for persistent storage.
                              If None, uses EphemeralClient (in-memory).
            embedding_model_name: Sentence transformer model for embeddings.
            embedding_backend: Embedding backend to use:
                              - 'sentence-transformers': Default PyTorch (~20-50ms)
                              - 'openvino': Intel-optimized, 2-4x faster (~5-15ms)
                              - 'onnx': Portable, ~1.5-2x faster (~10-25ms)
            preloaded_embedding_fn: Pre-loaded embedding function from ServiceCache.
                                   If provided, skips expensive model loading.
            preloaded_chroma_client: Pre-loaded ChromaDB client from ServiceCache.
                                    If provided (and no persist_directory), reuses client.
        """
        try:
            import chromadb
            from chromadb.utils import embedding_functions
        except ImportError as e:
            raise ImportError(
                "chromadb is required for ChromaIndex. "
                "Install with: pip install chromadb"
            ) from e

        self._index_name = index_name or f"chroma_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self._persist_directory = persist_directory
        self._embedding_model_name = embedding_model_name
        self._embedding_backend = self._resolve_embedding_backend(embedding_backend)

        # Initialize ChromaDB client - use preloaded if available
        if persist_directory:
            self._client = chromadb.PersistentClient(path=persist_directory)
            logger.info(f"Initialized ChromaDB with persistence at {persist_directory}")
        elif preloaded_chroma_client is not None:
            self._client = preloaded_chroma_client
            logger.info("Using preloaded ChromaDB EphemeralClient (shared)")
        else:
            self._client = chromadb.EphemeralClient()
            logger.info("Initialized ChromaDB EphemeralClient (in-memory)")

        # Setup embedding function - use preloaded if available (saves ~2s)
        if preloaded_embedding_fn is not None:
            self._embedding_fn = preloaded_embedding_fn
            logger.info("Using preloaded embedding function (fast init)")
        else:
            self._embedding_fn = self._create_embedding_function(
                embedding_model_name,
                embedding_functions,
            )

        # Get or create collection
        self._collection = self._client.get_or_create_collection(
            name=self._sanitize_collection_name(self._index_name),
            embedding_function=self._embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )
        self._is_setup = True

        logger.info(
            f"ChromaIndex initialized: collection={self._collection.name}, "
            f"embedding_model={embedding_model_name}, backend={self._embedding_backend}, "
            f"preloaded={preloaded_embedding_fn is not None}"
        )

    def _resolve_embedding_backend(
        self, embedding_backend: Optional[Union["EmbeddingBackend", str]]
    ) -> str:
        """Resolve embedding backend to string value."""
        if embedding_backend is None:
            return "sentence-transformers"
        if hasattr(embedding_backend, "value"):
            return embedding_backend.value
        return str(embedding_backend).lower()

    def _create_embedding_function(
        self,
        model_name: str,
        embedding_functions_module,
    ) -> Callable:
        """Create the appropriate embedding function based on backend."""
        backend = self._embedding_backend

        if backend == "openvino":
            try:
                return OpenVINOEmbeddingFunction(model_name=model_name)
            except Exception as e:
                logger.warning(
                    f"OpenVINO embedding failed ({e}), "
                    "falling back to sentence-transformers"
                )
                backend = "sentence-transformers"

        if backend == "onnx":
            try:
                return ONNXEmbeddingFunction(model_name=model_name)
            except Exception as e:
                logger.warning(
                    f"ONNX embedding failed ({e}), "
                    "falling back to sentence-transformers"
                )
                backend = "sentence-transformers"

        # Default: sentence-transformers
        return embedding_functions_module.SentenceTransformerEmbeddingFunction(
            model_name=model_name
        )

    @staticmethod
    def _sanitize_collection_name(name: str) -> str:
        """Sanitize collection name for ChromaDB requirements."""
        sanitized = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
        if len(sanitized) < 3:
            sanitized = f"col_{sanitized}"
        if len(sanitized) > 63:
            sanitized = sanitized[:63]
        return sanitized

    def should_refresh_index(self) -> bool:
        """Check if index should be refreshed based on document count."""
        count = self._collection.count()
        if count == 0:
            logger.info("ChromaDB collection is empty, refresh needed")
            return True
        logger.info(f"ChromaDB collection has {count} documents")
        return False

    async def index(self, docs: List[SearchDoc], deep_chunking: bool = False) -> str:
        """
        Index documents into ChromaDB collection.

        Args:
            docs: List of SearchDoc objects to index
            deep_chunking: Whether to apply deep chunking (not implemented for Chroma)

        Returns:
            Collection name
        """
        if not docs:
            logger.warning("No documents to index")
            return self._collection.name

        start_time = time.perf_counter()

        # Prepare documents for ChromaDB, deduplicating by ID
        seen_ids: dict[str, int] = {}
        ids = []
        documents = []
        metadatas = []

        for i, doc in enumerate(docs):
            doc_id = doc.document_id or f"doc_{i}_{int(time.time() * 1000)}"

            # Handle duplicate IDs by keeping only the last occurrence
            if doc_id in seen_ids:
                # Replace the previous entry with this one
                prev_idx = seen_ids[doc_id]
                documents[prev_idx] = doc.content
                metadatas[prev_idx] = {
                    "blurb": doc.blurb or "",
                    "source_type": doc.source_type or "",
                    "semantic_identifier": doc.semantic_identifier or "",
                    "url": doc.url or "",
                    "score": str(doc.score or 0.0),
                }
            else:
                seen_ids[doc_id] = len(ids)
                ids.append(doc_id)
                documents.append(doc.content)
                metadatas.append({
                    "blurb": doc.blurb or "",
                    "source_type": doc.source_type or "",
                    "semantic_identifier": doc.semantic_identifier or "",
                    "url": doc.url or "",
                    "score": str(doc.score or 0.0),
                })

        # Upsert to collection (handles both new and existing documents)
        self._collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(f"Indexed {len(docs)} documents in ChromaDB in {elapsed_ms:.2f}ms")

        return self._collection.name

    async def search(
        self,
        query: str,
        k: int = 3,
        **kwargs,
    ) -> List[SearchDoc]:
        """
        Search ChromaDB collection for relevant documents.

        Args:
            query: Search query string
            k: Number of results to return

        Returns:
            List of SearchDoc objects
        """
        if self._collection.count() == 0:
            logger.debug("ChromaDB collection is empty, returning empty results")
            return []

        start_time = time.perf_counter()

        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=min(k, self._collection.count()),
                include=["documents", "metadatas", "distances"],
            )

            search_docs = []
            if results and results.get("documents"):
                for i, doc_content in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
                    distance = results["distances"][0][i] if results.get("distances") else 0.0

                    # Convert distance to similarity score (cosine distance to similarity)
                    similarity_score = 1.0 - distance

                    search_doc = SearchDoc(
                        blurb=metadata.get("blurb", ""),
                        content=doc_content,
                        source_type=metadata.get("source_type", ""),
                        document_id=results["ids"][0][i] if results.get("ids") else f"result_{i}",
                        semantic_identifier=metadata.get("semantic_identifier", ""),
                        metadata=metadata,
                        url=metadata.get("url", ""),
                        score=similarity_score,
                    )
                    search_docs.append(search_doc)

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.info(f"ChromaDB search found {len(search_docs)} results in {elapsed_ms:.2f}ms")

            return search_docs

        except Exception as e:
            logger.error(f"ChromaDB search error: {e}")
            return []

    def search_sync(self, query: str, k: int = 3) -> List[SearchDoc]:
        """
        Synchronous search for use in non-async contexts (e.g., frame processors).

        Args:
            query: Search query string
            k: Number of results to return

        Returns:
            List of SearchDoc objects
        """
        if self._collection.count() == 0:
            return []

        start_time = time.perf_counter()

        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=min(k, self._collection.count()),
                include=["documents", "metadatas", "distances"],
            )

            search_docs = []
            if results and results.get("documents"):
                for i, doc_content in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
                    distance = results["distances"][0][i] if results.get("distances") else 0.0
                    similarity_score = 1.0 - distance

                    search_doc = SearchDoc(
                        blurb=metadata.get("blurb", ""),
                        content=doc_content,
                        source_type=metadata.get("source_type", ""),
                        document_id=results["ids"][0][i] if results.get("ids") else f"result_{i}",
                        semantic_identifier=metadata.get("semantic_identifier", ""),
                        metadata=metadata,
                        url=metadata.get("url", ""),
                        score=similarity_score,
                    )
                    search_docs.append(search_doc)

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.debug(f"ChromaDB sync search: {len(search_docs)} results in {elapsed_ms:.2f}ms")

            return search_docs

        except Exception as e:
            logger.error(f"ChromaDB sync search error: {e}")
            return []

    def clear(self) -> None:
        """Clear all documents from the collection."""
        self._client.delete_collection(self._collection.name)
        self._collection = self._client.get_or_create_collection(
            name=self._sanitize_collection_name(self._index_name),
            embedding_function=self._embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"Cleared ChromaDB collection: {self._collection.name}")

    @property
    def document_count(self) -> int:
        """Return the number of documents in the collection."""
        return self._collection.count()

    @property
    def is_initialized(self) -> bool:
        """Check if the index is properly initialized."""
        return self._is_setup

    @property
    def embedding_backend(self) -> str:
        """Return the embedding backend being used."""
        return self._embedding_backend
