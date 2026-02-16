import abc
import threading
from typing import Any

from super.core.indexing.models.base import BaseModel
from sentence_transformers import SentenceTransformer

# Module-level singleton for embedding model (shared across all instances)
_EMBEDDING_MODEL_SINGLETON = None
_EMBEDDING_MODEL_LOCK = threading.Lock()


class HFEmbeddingModel(BaseModel):
    def get_model(self, model_name: str = None) -> SentenceTransformer:
        """
        Get or create the singleton embedding model instance.
        This ensures the model is loaded only once per process, not per call.

        Returns:
            Shared SentenceTransformer instance
        """
        global _EMBEDDING_MODEL_SINGLETON, _EMBEDDING_MODEL_LOCK
        try:
            # Check if already initialized (fast path without lock)
            if _EMBEDDING_MODEL_SINGLETON is None:
                with _EMBEDDING_MODEL_LOCK:
                    # Double-check pattern to avoid race conditions
                    if _EMBEDDING_MODEL_SINGLETON is None:
                        def _load_model():
                            return SentenceTransformer(model_name)
                            # return SentenceTransformer(os.getenv('KB_EMBEDDING_MODEL', 'google/embeddinggemma-300m'))

                        _EMBEDDING_MODEL_SINGLETON = _load_model()

            return _EMBEDDING_MODEL_SINGLETON
        except Exception as e:
            print(f"Error getting embedding model: {e}")
            raise e
