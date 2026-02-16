from super.core.memory.store.chunker import (
    chunk_doc,
    batch_get_embedding,
    get_embedding,
)
from super.core.memory.store.base import BaseStore
from super.core.memory.models.document import SearchDoc
from typing import List, Any, Dict, Optional, Tuple
from openai import OpenAI
import os
from concurrent.futures import ThreadPoolExecutor
import logging
from functools import partial
import json
import duckdb
from datetime import datetime


class DuckDbMemory(BaseStore):
    def __init__(self, table_name=None, config=None, *args, **kwargs):
        self.memory_store = {}
        self.config = config or {
            "model_name": "all-MiniLM-L6-v2",
            "llm_api_key": os.getenv("OPENAI_API_KEY"),
            "llm_base_url": "https://api.openai.com/v1",
        }
        logging.basicConfig(level=logging.INFO)
        self.query = kwargs.get("query", None)
        self.table_name = kwargs.get("table_name", None)
        self.db_con = duckdb.connect(":memory:")

        self.db_con.install_extension("vss")
        self.db_con.load_extension("vss")
        self.db_con.install_extension("fts")
        self.db_con.load_extension("fts")
        self.db_con.sql("CREATE SEQUENCE seq_docid START 1000")
        self.embedding_dimensions = 1536

    def _create_table(self) -> str:
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")

        table_name = f"search_docs_{timestamp}"

        self.db_con.execute(
            f"""
            CREATE TABLE {table_name} (
                doc_id INTEGER PRIMARY KEY DEFAULT nextval('seq_docid'),
                document_id TEXT,
                content TEXT,
                semantic_identifier TEXT,

                blurb TEXT,
                source_type TEXT,
                metadata JSON,
                vec FLOAT[{self.embedding_dimensions}]
            );
            """
        )
        return table_name

    def add(self, docs: List[Any], ttl: Optional[int] = None) -> Dict[str, Any]:
        # Store TTL if provided

        all_chunks = chunk_doc(search_docs=docs)

        print("Chunks to save", len(all_chunks))
        client = OpenAI(
            api_key=self.config.get("llm_api_key"),
            base_url=self.config.get("llm_base_url"),
        )

        embed_batch_size = 50  # Save 5 SearchDoc instances in a batch
        query_batch_size = 100
        insert_data = []

        table_name = self._create_table()
        self.table_name = table_name

        batches: List[Tuple[str, List[SearchDoc]]] = []

        for doc in all_chunks:
            batches.append((doc.url, [doc]))

            # Process in batches of embed_batch_size
            if len(batches) >= embed_batch_size:
                with ThreadPoolExecutor(max_workers=10) as executor:
                    all_embeddings = list(
                        executor.map(partial(batch_get_embedding, client), batches)
                    )

                for chunk_batch, embeddings in all_embeddings:
                    url = chunk_batch[0]
                    list_chunks = chunk_batch[1]
                    insert_data.extend(
                        [
                            (
                                doc.document_id.replace("'", " "),
                                doc.content.replace("'", " "),
                                doc.semantic_identifier.replace("'", " "),
                                # doc.link.replace("'", " ") if doc.link else None,
                                doc.blurb.replace("'", " "),
                                doc.source_type.replace("'", " "),
                                json.dumps(doc.metadata).replace("'", " "),
                                embedding,
                            )
                            for doc, embedding in zip(list_chunks, embeddings)
                        ]
                    )
                batches.clear()  # Clear batches after processing

        # Handle any remaining documents that didn't fill a complete batch
        if batches:
            with ThreadPoolExecutor(max_workers=10) as executor:
                all_embeddings = list(
                    executor.map(partial(batch_get_embedding, client), batches)
                )

            for chunk_batch, embeddings in all_embeddings:
                url = chunk_batch[0]
                list_chunks = chunk_batch[1]
                insert_data.extend(
                    [
                        (
                            doc.document_id.replace("'", " "),
                            doc.content.replace("'", " "),
                            doc.semantic_identifier.replace("'", " "),
                            # doc.link.replace("'", " ") if doc.link else None,
                            doc.blurb.replace("'", " "),
                            doc.source_type.replace("'", " "),
                            json.dumps(doc.metadata).replace("'", " "),
                            embedding,
                        )
                        for doc, embedding in zip(list_chunks, embeddings)
                    ]
                )

        for i in range(0, len(insert_data), query_batch_size):
            value_str = ", ".join(
                [
                    f"('{document_id}', '{content}', '{semantic_identifier}','{blurb}', '{source_type}', '{metadata}', {embedding})"
                    for document_id, content, semantic_identifier, blurb, source_type, metadata, embedding in insert_data[
                        i : i + query_batch_size
                    ]
                ]
            )
            query = f"""
            INSERT INTO {table_name} (document_id, content, semantic_identifier,blurb, source_type, metadata, vec) VALUES {value_str};
            """
            self.db_con.execute(query)

        self.db_con.execute(
            f"""
                CREATE INDEX {table_name}_cos_idx ON {table_name} USING HNSW (vec)
                WITH (metric = 'cosine');
            """
        )

        return {"status": "success", "added_chunks": len(all_chunks)}

    def get(self, key: str) -> Any:
        return self.memory_store.get(key)

    def delete(self, key: str) -> Any:
        return self.memory_store.pop(key, None)

    def search(self, query: str) -> List[Any]:
        client = OpenAI(
            api_key=self.config.get("llm_api_key"),
            base_url=self.config.get("llm_base_url"),
        )
        embeddings = get_embedding(client, [query])[0]
        # embeddings = self.create_embedding([query])[0]

        # Perform vector search using DuckDB
        query_result: duckdb.DuckDBPyRelation = self.db_con.sql(
            f"""
            SELECT * FROM {self.table_name}
            ORDER BY array_distance(vec, {embeddings}::FLOAT[{self.embedding_dimensions}])
            LIMIT 10;
            """
        )

        self.logger.debug(query_result)

        matched_docs_dict = {}

        # Create SearchDoc instances from the vector search results
        for vec_result in query_result.fetchall():
            # self.logger.info(f"Vector search result: {type(vec_result[7])}\n\n")
            doc_id = vec_result[0]
            search_doc = SearchDoc(
                document_id=str(vec_result[1]) + "__" + str(doc_id),
                content=vec_result[2],
                semantic_identifier=vec_result[3],
                # link=vec_result[4],
                blurb=vec_result[4],
                source_type=vec_result[5],
                metadata=vec_result[6],  # Assuming metadata is stored as JSON
            )
            matched_docs_dict[doc_id] = search_doc

        # if settings.hybrid_search:

        return list(matched_docs_dict.values())


# Example usage
if __name__ == "__main__":
    chunk_memory = DuckDbMemory()

    # Adding documents
    result = chunk_memory.add(
        ["This is a test document.\nIt has multiple lines.", "Another document."],
        ttl=60,
    )
    print(result)

    # Searching for a chunk
    search_results = chunk_memory.search("test")
    print(search_results)

    # Retrieving a specific chunk
    specific_chunk = chunk_memory.get("some_unique_key")
    print(specific_chunk)

    # Deleting a specific chunk
    deleted_chunk = chunk_memory.delete("some_unique_key")
    print(deleted_chunk)
