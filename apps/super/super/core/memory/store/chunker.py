from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List, Any, Dict, Tuple

from chonkie import Chunk, TokenChunker, SDPMChunker
from super.core.memory.models.document import SearchDoc
from openai import OpenAI


def chunk_doc(
    search_docs: Optional[List[SearchDoc]] = None, config: Dict = None
) -> List[SearchDoc] | None:
    # Retrieve documents if not provided

    # Define a helper function for chunking to allow concurrent processing
    def chunk_document(doc):
        model = config.get("model_name", None)
        chunker = SDPMChunker(
            embedding_model=model,
            skip_window=2,
            max_chunk_size=512,
            similarity_threshold=0.5,
        )
        chunks = chunker.chunk(doc.content)

        return [
            SearchDoc(
                blurb=doc.blurb,
                content=chunk.text,
                source_type=doc.source_type,
                document_id=f"{doc.document_id}_chunk_{idx}",  # Unique ID for each chunked document
                semantic_identifier=doc.semantic_identifier,
                metadata=doc.metadata,
                url=doc.url,
                score=doc.score,
            )
            for idx, chunk in enumerate(chunks)
        ]

    # Process documents in parallel and gather all SearchDoc instances in a single list
    with ThreadPoolExecutor() as executor:
        results = executor.map(chunk_document, search_docs)

    # Flatten the results into a single list of SearchDocs for minimal time complexity
    new_search_docs = [
        search_doc for chunked_docs in results for search_doc in chunked_docs
    ]

    return new_search_docs


def get_embedding(self, client: "OpenAI", texts: List[str]) -> List[List[float]]:
    if len(texts) == 0:
        return []

    response = client.embeddings.create(input=texts, model=self.embedding_model)
    embeddings = [response.data[i].embedding for i in range(len(response.data))]
    return embeddings


def batch_get_embedding(
    self, client: "OpenAI", chunk_batch: Tuple[str, List[SearchDoc]]
) -> Tuple[Tuple[str, List[SearchDoc]], List[List[float]]]:
    texts = [doc.content for doc in chunk_batch[1]]
    embeddings = self.get_embedding(client, texts)
    # embeddings = self.create_embedding(texts)
    # Keep the original chunk batch intact
    return chunk_batch, embeddings
