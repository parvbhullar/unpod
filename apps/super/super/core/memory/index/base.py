from abc import ABC, abstractmethod
from typing import List
from super.core.memory.schema import BaseDocument


class BaseIndex(ABC):
    """Abstract base class for vector index implementations."""

    @abstractmethod
    def index(self, chunks: List[BaseDocument]) -> str:
        """Save chunks to the index and return the table/index name."""
        pass

    @abstractmethod
    def search(self, query: str, k: int = 10) -> List[BaseDocument]:
        """Search the index with the given query and return relevant documents."""
        pass
