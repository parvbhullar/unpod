"""
Knowledge Base Tool - Document and knowledge retrieval.

Provides knowledge retrieval functionality that works with any orchestrator.
This is a generic interface that can connect to various knowledge stores.
"""

from typing import Any, Dict, List, Optional

from super.core.logging import logging as app_logging
from super.core.tools.base import BaseTool, ToolCategory, ToolResult

logger = app_logging.get_logger("tools.knowledge_base")


class KnowledgeBaseTool(BaseTool):
    """
    Tool for querying a knowledge base.

    This is a generic implementation that can be extended to connect
    to various knowledge stores (vector DB, document store, etc.).
    """

    name = "query_knowledge_base"
    description = "Query the knowledge base for relevant information"
    category = ToolCategory.KNOWLEDGE

    def __init__(
        self,
        retriever: Optional[Any] = None,
        top_k: int = 5,
    ) -> None:
        self._retriever = retriever
        self._top_k = top_k

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Query to search for relevant documents",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": f"Number of results to return (default: {self._top_k})",
                    },
                    "filters": {
                        "type": "object",
                        "description": "Optional metadata filters",
                    },
                },
                "required": ["query"],
            },
        }

    async def execute(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> ToolResult:
        k = top_k or self._top_k

        if not self._retriever:
            return ToolResult(
                success=False,
                error="No knowledge base retriever configured",
            )

        try:
            if hasattr(self._retriever, "ainvoke"):
                docs = await self._retriever.ainvoke(query)
            elif hasattr(self._retriever, "invoke"):
                docs = self._retriever.invoke(query)
            elif hasattr(self._retriever, "get_relevant_documents"):
                docs = await self._retriever.aget_relevant_documents(query)
            else:
                return ToolResult(
                    success=False,
                    error="Retriever does not have a compatible interface",
                )

            results: List[Dict[str, Any]] = []
            for doc in docs[:k]:
                results.append(
                    {
                        "content": getattr(doc, "page_content", str(doc)),
                        "metadata": getattr(doc, "metadata", {}),
                    }
                )

            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "results": results,
                    "count": len(results),
                },
            )

        except Exception as e:
            logger.error(f"Knowledge base query error: {e}")
            return ToolResult(success=False, error=f"Query failed: {e}")
