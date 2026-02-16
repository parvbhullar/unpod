"""Abstract interface for document loader implementations."""

from abc import ABC, abstractmethod
from typing import Any, Iterator, List, Optional


class BaseLoader(ABC):
    """Interface for loading documents."""

    @abstractmethod
    def load(self) -> List[Any]:
        """Load data into document objects."""

    def load_and_split(self, text_splitter: Optional[Any] = None) -> List[Any]:
        """Load documents and split into chunks."""
        if text_splitter is None:
            _text_splitter = None
        else:
            _text_splitter = text_splitter
        docs = self.load()
        return _text_splitter.split_documents(docs)

    def lazy_load(self) -> Iterator[Any]:
        """A lazy loader for document content."""
        raise NotImplementedError(
            f"{self.__class__.__name__} does not implement lazy_load()"
        )
