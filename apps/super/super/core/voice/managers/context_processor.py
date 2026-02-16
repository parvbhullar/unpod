import time
import os
from pipecat.frames.frames import (
    TranscriptionFrame
)
from pipecat.processors.frame_processor import (
    FrameProcessor
)

from super.core.voice.schema import UserState


class FAISSContextProcessor(FrameProcessor):
    def __init__(self, voice_handler):
        super().__init__()
        self.voice_handler = voice_handler
        self._logger = voice_handler._logger

    async def process_frame(self, frame, direction):
        # Process transcription frames and add FAISS context
        if isinstance(frame, TranscriptionFrame):
            try:
                # Get transcription text
                transcription_text = frame.text
                if not transcription_text or len(transcription_text.strip()) < 3:
                    return [frame]

                self._logger.info(f"Processing transcription for FAISS context: {transcription_text[:50]}...")

                # Search in FAISS for relevant context
                faiss_start = time.time()
                search_results = await self.voice_handler._context_retrieval.search_context(
                    query_embedding=self.voice_handler._embedding_model.encode([transcription_text],
                                                                               convert_to_tensor=False),
                    k=2,  # Get top 2 results for context
                    use_cache=True
                )

                faiss_time = (time.time() - faiss_start) * 1000

                # Process results and add context
                chunk_ids, search_metrics = search_results
                context_docs = []
                for chunk_id in chunk_ids:
                    chunk = self.voice_handler._context_retrieval._hot_chunks.get(str(chunk_id))
                    if chunk and chunk.get("content"):
                        context_docs.append(chunk["content"])

                # Add FAISS context to transcription if found
                if context_docs:
                    enhanced_text = f"""
                        Context from knowledge base:
                        {chr(10).join(context_docs)}

                        User: {transcription_text}
                        """
                    # Update the transcription frame with enhanced content
                    frame.text = enhanced_text
                    self._logger.info(f"Added FAISS context ({len(context_docs)} docs) in {faiss_time:.2f}ms")
                else:
                    self._logger.info(f"No FAISS context found in {faiss_time:.2f}ms")

            except Exception as e:
                self._logger.error(f"Error in FAISS context processing: {e}")

        return [frame]


# return FAISSContextProcessor(self)

    async def _add_faiss_context_to_transcript(self, transcript_text: str) -> str:
        """Add FAISS context to transcript text before sending to LLM"""
        import time

        try:
            if not transcript_text or len(transcript_text.strip()) < 3:
                return transcript_text

            if not self._context_retrieval or not self._embedding_model:
                return transcript_text

            self._logger.info(f"Adding FAISS context to transcript: {transcript_text[:50]}...")

            # Search in FAISS for relevant context
            faiss_start = time.time()
            search_results = await self._context_retrieval.search_context(
                query_embedding=self._embedding_model.encode([transcript_text], convert_to_tensor=False),
                k=2,  # Get top 2 results for context
                use_cache=True
            )

            faiss_time = (time.time() - faiss_start) * 1000

            # Process results and add context
            chunk_ids, search_metrics = search_results
            context_docs = []
            for chunk_id in chunk_ids:
                chunk = self._context_retrieval._hot_chunks.get(str(chunk_id))
                if chunk and chunk.get("content"):
                    context_docs.append(chunk["content"])

            # Add FAISS context to transcript if found
            if context_docs:
                enhanced_text = f"""
                Context from knowledge base:
                {chr(10).join(context_docs)}

                User: {transcript_text}
                """
                self._logger.info(f"Added FAISS context ({len(context_docs)} docs) in {faiss_time:.2f}ms")
                return enhanced_text
            else:
                self._logger.info(f"No FAISS context found in {faiss_time:.2f}ms")
                return transcript_text

        except Exception as e:
            self._logger.error(f"Error adding FAISS context to transcript: {e}")
            return transcript_text

    async def _preload_knowledge_base_documents(self, user_state: UserState):
        import time
        import requests

        preload_start = time.time()

        try:
            # Get all knowledge bases from user_state
            kn_list = getattr(user_state, 'knowledge_base', [])
            token = getattr(user_state, 'token', None)

            if not kn_list and not token:
                self._logger.info("No knowledge bases or token found, skipping document preload")
                return True

            # Collect all knowledge base tokens
            kn_bases = []
            for item in kn_list:
                if item.get("token"):
                    kn_bases.append(item["token"])

            if token:
                kn_bases.append(token)

            if not kn_bases:
                self._logger.info("No valid knowledge base tokens found, skipping document preload")
                return True

            self._logger.info(f"Pre-loading documents from {len(kn_bases)} knowledge bases: {kn_bases}")

            total_docs_loaded = 0

            # Load documents from all knowledge bases with meaningful queries
            try:
                # Get knowledge base names for meaningful queries
                knowledge_base_names = []
                for kb_item in kn_list:
                    kb_name = kb_item.get("name", "")
                    if kb_name:
                        knowledge_base_names.append(kb_name)

                # Create meaningful queries using knowledge base names
                queries = []
                for kb_name in knowledge_base_names:
                    queries.extend([
                        f"{kb_name} overview",
                        f"About {kb_name}",
                        f"{kb_name} information"
                    ])

                # Also add some general queries
                queries.extend([
                    "general information",
                    "product details",
                    "specifications"
                ])

                # Remove duplicates and limit to avoid too many API calls
                queries = list(set(queries))[:10]  # Max 10 queries

                self._logger.info(f"Pre-loading with {len(queries)} meaningful queries: {queries[:3]}...")

                # Try each query until we get some documents
                total_docs_loaded = 0
                for query in queries:
                    try:
                        # Use the same remote search logic but with meaningful query
                        payload = {"query": query, "kn_bases": kn_bases}
                        # Debug: Print the DOC_SEARCH_URL being used
                        doc_search_url = os.getenv("DOC_SEARCH_URL", "")
                        print(
                            f"DEBUG: Pre-loading with query '{query}' using DOC_SEARCH_URL: {repr(doc_search_url)}")
                        if not doc_search_url:
                            print("WARNING: DOC_SEARCH_URL is empty, using fallback URL")
                            doc_search_url = "http://qa-search-service.co/api/v1/search/query/docs/"

                        response = requests.post(doc_search_url, json=payload, timeout=10)

                        if response.status_code == 200:
                            result = response.json()
                            docs = result.get("data", {}).get("search_response_summary", {}).get("top_sections", [])

                            if docs:
                                # Cache these documents in FAISS
                                await self._cache_remote_results(result)
                                total_docs_loaded += len(docs)
                                self._logger.info(
                                    f"Pre-loaded {len(docs)} documents using query '{query}' from {len(kn_bases)} knowledge bases: {kn_bases}")
                                break  # Success, no need to try more queries
                            else:
                                self._logger.warning(
                                    f"No documents found for query '{query}' in {len(kn_bases)} knowledge bases: {kn_bases}")
                        else:
                            self._logger.warning(
                                f"Failed to fetch documents for query '{query}' from {len(kn_bases)} knowledge bases {kn_bases}: {response.status_code}")

                    except Exception as e:
                        self._logger.warning(f"Error pre-loading with query '{query}': {e}")
                        continue

                if total_docs_loaded > 0:
                    self._logger.info(
                        f"✅ Successfully pre-loaded {total_docs_loaded} documents using meaningful queries")
                else:
                    self._logger.warning("No documents were pre-loaded with any query")

            except Exception as e:
                self._logger.error(f"Error pre-loading documents from knowledge bases {kn_bases}: {e}")

            preload_time = (time.time() - preload_start) * 1000

            if total_docs_loaded > 0:
                self._logger.info(
                    f"✅ Successfully pre-loaded {total_docs_loaded} documents in {preload_time:.2f}ms")
                return True
            else:
                self._logger.warning("No documents were pre-loaded")
                return True

        except Exception as e:
            self._logger.error(f"Error in document pre-loading: {e}")
            return False

    async def _get_index(self, query: str, kn_bases: list = None) -> dict:
        import numpy as np
        import html
        import time

        start_time = time.time()

        # Initialize context retrieval if not already done
        if self._context_retrieval is None or self._embedding_model is None:
            try:
                await self._init_context_retrieval()
            except Exception as e:
                self._logger.error(f"Failed to initialize context retrieval, falling back to remote search: {e}")
                return await self._fallback_remote_search(query, kn_bases)

        try:
            # Get query embedding
            embedding_start = time.time()
            query_embedding = self._embedding_model.encode([query], convert_to_tensor=False)
            embedding_time = (time.time() - embedding_start) * 1000

            # Search in the context retrieval system
            search_start = time.time()
            search_results = await self._context_retrieval.search_context(
                query_embedding=query_embedding,
                k=3,  # Return top 3 results
                use_cache=True
            )

            search_time = (time.time() - search_start) * 1000

            # Process results
            chunk_ids, search_metrics = search_results
            results = []
            for i, chunk_id in enumerate(chunk_ids):
                chunk = self._context_retrieval._hot_chunks.get(str(chunk_id))
                if chunk:
                    results.append({
                        "combined_content": chunk.get("content", ""),
                        "score": 0.8,  # Default score since we don't have distances from search_context
                        "content": chunk.get("content", ""),
                        "recency_bias": 1.0
                    })

            total_time = (time.time() - start_time) * 1000

            if results:
                self._logger.info(
                    f"FAISS search completed in {total_time:.2f}ms (embedding: {embedding_time:.2f}ms, search: {search_time:.2f}ms)")
                return {"data": {"search_response_summary": {"top_sections": results[:3]}}}

            self._logger.info(f"FAISS search found no results in {total_time:.2f}ms, falling back to remote search")
            return await self._fallback_remote_search(query, kn_bases)
        except Exception as e:
            self._logger.error(f"Error in context retrieval: {e}")
            return await self._fallback_remote_search(query, kn_bases)

    async def _fallback_remote_search(self, query: str, kn_bases: list = None) -> dict:
        """Fallback to remote search when local search has no results"""
        import html
        import requests

        self._logger.info("Falling back to remote search")
        payload = {"query": query, "kn_bases": kn_bases or []}

        # Debug: Print the DOC_SEARCH_URL being used
        doc_search_url = os.getenv("DOC_SEARCH_URL", "")
        print(f"DEBUG: Fallback search using DOC_SEARCH_URL: {repr(doc_search_url)}")
        if not doc_search_url:
            print("WARNING: DOC_SEARCH_URL is empty in fallback, using fallback URL")
            doc_search_url = "http://qa-search-service.co/api/v1/search/query/docs/"

        response = requests.post(doc_search_url, json=payload)

        if response.status_code != 200:
            return {
                "error": str(response.status_code),
                "message": "Internal error retrieving information.",
            }

        try:
            result = response.json()
            # Cache the remote results in our context retrieval system
            await self._cache_remote_results(result)
            return result
        except Exception as e:
            self._logger.error(f"Error processing remote search results: {e}")
            return {"data": {"search_response_summary": {"top_sections": []}}}


