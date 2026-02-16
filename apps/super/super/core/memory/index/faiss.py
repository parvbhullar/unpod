import asyncio
import os
from datetime import datetime
from typing import List, Optional, Set, Any
import re

from langchain_core.documents import Document
from super.core.indexing.models.factory import ModelFactory, ModelProviderType
from super.core.memory.index.base import BaseIndex
from super.core.memory.search.schema import SearchDoc
from super.core.utils.logger import setup_logger
from super.core.utils.timing import log_function_time
from langchain_community.vectorstores import FAISS

logger = setup_logger()


class FaissIndex(BaseIndex):
    """FAISS-based vector index implementation."""

    def __init__(
        self,
        index_name: str = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        refresh_index: bool = False,
    ):
        """
        Initialize FAISS index with optional API configuration.

        Args:
            index_name: Name for the index (uses timestamp if not provided)
            api_key: Optional API key
            base_url: Optional base URL
            refresh_index: If False (default), reuse existing index if < 24 hours old
        """
        self.api_key = api_key
        self.base_url = base_url
        self.refresh_index = refresh_index
        self.embedding_model = ModelFactory.factory(
            model_name="all-MiniLM-L6-v2",
        )

        # self._chunker = self.load_chunker()
        # ✅ FIXED: Don't create timestamp-based index if index_name is provided
        # Use provided index_name or create new one with timestamp
        if index_name:
            self._index_name = f"faiss_memory/{index_name}"
        else:
            timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
            self._index_name = f"faiss_memory/search_docs_{timestamp}"

    def load_chunker(self) -> Any:
        # TODO replace this with super chunker
        raise NotImplementedError("Chunker loading not implemented yet.")
        # return SDPMChunker(
        #     embedding_model=self.load_embedding_model(),
        #     skip_window=2,
        #     max_chunk_size=1024,
        #     similarity_threshold=0.5,
        #     initial_sentences=10,
        # )

    def load_embedding_model(self, model_name: str = "all-MiniLM-L6-v2") -> Any:
        if self.embedding_model:
            return self.embedding_model
        return ModelFactory.factory(
            model_name=model_name, model_provider_type=ModelProviderType.openai
        )

    def should_refresh_index(self) -> bool:
        """
        Determine if the index should be refreshed based on age and configuration.

        Returns:
            True if index should be refreshed, False if existing index can be used
        """
        # If refresh_index is explicitly True, always refresh
        if self.refresh_index:
            logger.info("Index refresh forced by configuration (refresh_index=True)")
            return True

        # Check if index exists
        index_file = os.path.join(self._index_name, "index.faiss")
        if not os.path.exists(index_file):
            logger.info(f"Index does not exist at {index_file}, creating new index")
            return True

        # Check index age (24 hours = 86400 seconds)
        try:
            index_mtime = os.path.getmtime(index_file)
            age_seconds = datetime.now().timestamp() - index_mtime
            age_hours = age_seconds / 3600

            if age_seconds > 86400:  # 24 hours
                logger.info(f"Index is {age_hours:.1f} hours old (> 24h), refreshing")
                return True
            else:
                logger.info(f"Index is {age_hours:.1f} hours old (< 24h), reusing existing index")
                return False
        except Exception as e:
            logger.warning(f"Could not check index age: {e}, refreshing to be safe")
            return True

    @staticmethod
    def convert_to_document(search_doc: SearchDoc) -> Document:
        """Convert a SearchDoc to a LangChain Document."""
        return Document(
            page_content=search_doc.content,
            metadata={
                "blurb": search_doc.blurb,
                "source_type": search_doc.source_type,
                "document_id": search_doc.document_id,
                "semantic_identifier": search_doc.semantic_identifier,
                "metadata": search_doc.metadata,
                "url": search_doc.url,
                "score": search_doc.score,
            },
        )

    @staticmethod
    def convert_to_search_doc(document: Document) -> SearchDoc:
        """Convert a LangChain Document back to SearchDoc."""
        metadata = document.metadata
        return SearchDoc(
            blurb=metadata.get("blurb"),
            content=document.page_content,
            source_type=metadata.get("source_type"),
            document_id=metadata.get("document_id"),
            semantic_identifier=metadata.get("semantic_identifier"),
            metadata=metadata.get("metadata"),
            url=metadata.get("url"),
            score=metadata.get("score", 0.01),
        )

    @log_function_time(print_only=True)
    async def index(self, docs: List[SearchDoc], deep_chunking: bool = False) -> str:
        """Save chunks to FAISS index and return the table name."""

        if deep_chunking:
            chunks = await self.chunk_docs(docs)
        else:
            chunks = docs

        logger.info(f"Saving {len(chunks)} chunks to FAISS index")
        # Convert SearchDocs to LangChain Documents
        documents = [self.convert_to_document(doc) for doc in chunks]

        # Initialize and populate FAISS index
        faiss_index = FAISS.from_documents(documents, self.embedding_model)

        # embedding_dim = len(self.embedding_model.embed_query("hello world"))
        # index = faiss.IndexFlatL2(embedding_dim)
        # #
        # vector_store = FAISS(
        #     embedding_function=self.embedding_model,
        #     index=index,
        #     docstore=InMemoryDocstore(),
        #     index_to_docstore_id={},
        # )

        # Save the index
        logger.info(f"Saving FAISS index to {self._index_name}")
        faiss_index.save_local(self._index_name)
        return self._index_name

    @log_function_time(print_only=True)
    async def search(
        self,
        query: str,
        k: int = 10,
        **kwargs,
    ) -> List[SearchDoc]:
        """Search FAISS index with query and return relevant documents."""
        try:
            # Check if index file exists
            index_file = os.path.join(self._index_name, "index.faiss")
            if not os.path.exists(index_file):
                logger.info(f"Index file not found at {index_file}, returning empty results")
                return []

            # Load the index
            loaded_faiss_index = FAISS.load_local(
                self._index_name,
                self.embedding_model,
                allow_dangerous_deserialization=True,
            )

            # Generate query embedding and search
            query_embedding = self.embedding_model.embed_query(query)
            results = loaded_faiss_index.similarity_search_by_vector(
                query_embedding, k=k
            )

            # Convert results back to SearchDocs and ensure uniqueness
            unique_search_docs: Set[SearchDoc] = {
                self.convert_to_search_doc(doc) for doc in results
            }

            logger.info(f"Found {len(unique_search_docs)} unique documents")
            return list(unique_search_docs)

        except Exception as e:
            logger.error(f"Error searching index: {str(e)}")
            return []

    async def chunk_docs(self, search_docs: List[SearchDoc]) -> List[SearchDoc]:
        """Chunk and index search documents."""

        new_search_docs = []

        async def process_document(doc):
            chunks = self._chunker.chunk(self.clean_content(doc.content))
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

        async def process_all_documents():
            tasks = [process_document(doc) for doc in search_docs]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    print(f"Error processing a document: {result}")
                else:
                    new_search_docs.extend(result)

        await process_all_documents()

        return new_search_docs

    def clean_content(self, content: str) -> str:
        """Cleans the input content."""
        cleaned = content.strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        cleaned = cleaned.replace("{", "").replace("}", "")
        return cleaned
