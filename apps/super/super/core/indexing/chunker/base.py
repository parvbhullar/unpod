import abc

from super.core.indexing.schema import DocAwareChunk
from super.core.memory.schema import BaseDocument


class BaseChunker:
    @abc.abstractmethod
    def chunk(self, document: BaseDocument) -> list[DocAwareChunk]:
        raise NotImplementedError
