"""
Vector index factory for switching between FAISS and ChromaDB backends.

Usage:
    from super.core.memory.index.factory import create_vector_index, VectorBackend

    # Create index based on env variable VECTOR_BACKEND (default: faiss)
    index = create_vector_index(index_name="my_index")

    # Or specify backend explicitly
    index = create_vector_index(
        index_name="my_index",
        backend=VectorBackend.CHROMA
    )

    # With OpenVINO embeddings for 2-4x faster inference
    index = create_vector_index(
        index_name="my_index",
        backend=VectorBackend.CHROMA,
        embedding_backend=EmbeddingBackend.OPENVINO
    )

Environment Variables:
    VECTOR_BACKEND: 'faiss' or 'chroma' (default: 'faiss')
    EMBEDDING_BACKEND: 'sentence-transformers', 'openvino', or 'onnx' (default: 'sentence-transformers')
    CHROMA_PERSIST_DIR: Directory for ChromaDB persistence (optional)
"""

import os
from enum import Enum
from typing import Optional, Union

from super.core.memory.index.base import BaseIndex
from super.core.utils.logger import setup_logger

logger = setup_logger()


class VectorBackend(str, Enum):
    """Supported vector database backends."""

    FAISS = "faiss"
    CHROMA = "chroma"


class EmbeddingBackend(str, Enum):
    """Supported embedding backends for local inference."""

    SENTENCE_TRANSFORMERS = "sentence-transformers"  # Default PyTorch
    OPENVINO = "openvino"  # Intel-optimized, 2-4x faster on CPU
    ONNX = "onnx"  # Portable, ~1.5-2x faster


def create_vector_index(
    index_name: str,
    backend: Optional[Union[VectorBackend, str]] = None,
    refresh_index: bool = False,
    embedding_backend: Optional[Union[EmbeddingBackend, str]] = None,
    use_preloaded: bool = True,
    **kwargs,
) -> BaseIndex:
    """
    Create a vector index instance based on the specified backend.

    Args:
        index_name: Name for the index/collection
        backend: Vector backend to use. If None, reads from VECTOR_BACKEND env var
                 (defaults to 'faiss')
        refresh_index: Whether to refresh/recreate the index
        embedding_backend: Embedding backend for ChromaDB. If None, reads from
                          EMBEDDING_BACKEND env var (defaults to 'sentence-transformers')
                          Options: 'sentence-transformers', 'openvino', 'onnx'
        use_preloaded: If True, attempts to use preloaded embedding function and
                       ChromaDB client from ServiceCache (faster init). Default: True
        **kwargs: Additional arguments passed to the index constructor

    Returns:
        BaseIndex implementation (FaissIndex or ChromaIndex)

    Environment Variables:
        VECTOR_BACKEND: 'faiss' or 'chroma' (default: 'faiss')
        EMBEDDING_BACKEND: 'sentence-transformers', 'openvino', 'onnx' (default: 'sentence-transformers')
        CHROMA_PERSIST_DIR: Directory for ChromaDB persistence (optional)
    """
    if backend is None:
        backend_str = os.getenv("VECTOR_BACKEND", "faiss").lower()
        try:
            backend = VectorBackend(backend_str)
        except ValueError:
            logger.warning(
                f"Invalid VECTOR_BACKEND '{backend_str}', falling back to faiss"
            )
            backend = VectorBackend.FAISS
    elif isinstance(backend, str):
        try:
            backend = VectorBackend(backend.lower())
        except ValueError:
            logger.warning(f"Invalid backend '{backend}', falling back to faiss")
            backend = VectorBackend.FAISS

    # Resolve embedding backend
    resolved_embedding_backend = _resolve_embedding_backend(embedding_backend)

    logger.info(f"Creating vector index with backend: {backend.value}")

    if backend == VectorBackend.CHROMA:
        return _create_chroma_index(
            index_name,
            embedding_backend=resolved_embedding_backend,
            use_preloaded=use_preloaded,
            **kwargs
        )
    else:
        return _create_faiss_index(index_name, refresh_index, **kwargs)


def _resolve_embedding_backend(
    embedding_backend: Optional[Union[EmbeddingBackend, str]] = None,
) -> EmbeddingBackend:
    """Resolve embedding backend from argument or environment variable."""
    if embedding_backend is None:
        backend_str = os.getenv("EMBEDDING_BACKEND", "sentence-transformers").lower()
        try:
            return EmbeddingBackend(backend_str)
        except ValueError:
            logger.warning(
                f"Invalid EMBEDDING_BACKEND '{backend_str}', "
                "falling back to sentence-transformers"
            )
            return EmbeddingBackend.SENTENCE_TRANSFORMERS
    elif isinstance(embedding_backend, str):
        try:
            return EmbeddingBackend(embedding_backend.lower())
        except ValueError:
            logger.warning(
                f"Invalid embedding_backend '{embedding_backend}', "
                "falling back to sentence-transformers"
            )
            return EmbeddingBackend.SENTENCE_TRANSFORMERS
    return embedding_backend


def _create_faiss_index(
    index_name: str,
    refresh_index: bool = False,
    **kwargs,
) -> BaseIndex:
    """Create a FAISS index instance."""
    from super.core.memory.index.faiss import FaissIndex

    return FaissIndex(
        index_name=index_name,
        refresh_index=refresh_index,
        api_key=kwargs.get("api_key"),
        base_url=kwargs.get("base_url"),
    )


def _create_chroma_index(
    index_name: str,
    embedding_backend: EmbeddingBackend = EmbeddingBackend.SENTENCE_TRANSFORMERS,
    use_preloaded: bool = True,
    **kwargs,
) -> BaseIndex:
    """
    Create a ChromaDB index instance.

    Args:
        index_name: Name for the collection
        embedding_backend: Embedding backend to use
        use_preloaded: If True, attempts to use preloaded resources from ServiceCache
        **kwargs: Additional arguments

    Returns:
        ChromaIndex instance
    """
    from super.core.memory.index.chroma import ChromaIndex

    persist_directory = kwargs.get(
        "persist_directory",
        os.getenv("CHROMA_PERSIST_DIR"),
    )
    embedding_model = kwargs.get(
        "embedding_model_name",
        "all-MiniLM-L6-v2",
    )

    # Try to get preloaded resources from ServiceCache
    preloaded_embedding_fn = None
    preloaded_chroma_client = None

    if use_preloaded and not persist_directory:
        try:
            from super.core.voice.voice_agent_handler import get_service_cache

            cache = get_service_cache()
            if cache.is_embedding_loaded:
                preloaded_embedding_fn = cache.get_embedding_fn()
                preloaded_chroma_client = cache.get_chroma_client()
                logger.info(
                    f"Using preloaded embedding function from ServiceCache "
                    f"(loaded in {cache.embedding_load_time_ms:.0f}ms)"
                )
        except ImportError:
            # ServiceCache not available (e.g., non-voice context)
            pass
        except Exception as e:
            logger.warning(f"Could not get preloaded resources: {e}")

    logger.info(f"Creating ChromaIndex with embedding backend: {embedding_backend.value}")

    return ChromaIndex(
        index_name=index_name,
        persist_directory=persist_directory,
        embedding_model_name=embedding_model,
        embedding_backend=embedding_backend,
        preloaded_embedding_fn=preloaded_embedding_fn,
        preloaded_chroma_client=preloaded_chroma_client,
    )


def get_default_backend() -> VectorBackend:
    """Get the default vector backend from environment."""
    backend_str = os.getenv("VECTOR_BACKEND", "faiss").lower()
    try:
        return VectorBackend(backend_str)
    except ValueError:
        return VectorBackend.FAISS
