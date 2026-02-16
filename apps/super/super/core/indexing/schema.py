from pydantic import BaseModel

from super.core.memory.schema import BaseDocument

Embedding = list[float]


class ChunkEmbedding(BaseModel):
    full_embedding: Embedding
    mini_chunk_embeddings: list[Embedding]


class BaseChunk(BaseModel):
    chunk_id: int
    blurb: str  # The first sentence(s) of the first Section of the chunk
    content: str
    source_links: dict[
        int, str
    ] | None  # Holds the link and the offsets into the raw Chunk text
    section_continuation: bool  # True if this Chunk's start is not at the start of a Section


class DocAwareChunk(BaseChunk):
    # During indexing flow, we have access to a complete "Document"
    # During inference we only have access to the document id and do not reconstruct the Document
    source_document: BaseDocument

    def to_short_descriptor(self) -> str:
        """Used when logging the identity of a chunk"""
        return (
            f"Chunk ID: '{self.chunk_id}'; {self.source_document.to_short_descriptor()}"
        )


class IndexChunk(DocAwareChunk):
    embeddings: ChunkEmbedding
    title_embedding: Embedding | None
