"""
Exa Tool - Web search and people discovery.

Provides semantic web search using Exa AI's APIs.
This tool is stateless and can be used with any orchestrator.
"""

from typing import Any, Dict, List, Optional

from super.core.logging import logging as app_logging
from super.core.tools.base import BaseTool, ToolCategory, ToolResult

logger = app_logging.get_logger("tools.exa")


def _extract_source_from_url(url: str) -> Optional[str]:
    """Extract domain name from URL."""
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        domain = parsed.netloc
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return None


class ExaWebSearchTool(BaseTool):
    """
    Tool for web search using Exa AI's semantic search.

    Supports category filtering and returns AI summaries.
    """

    name = "search_web"
    description = "Search the web using Exa's semantic search"
    category = ToolCategory.SEARCH

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query in natural language",
                    },
                    "category": {
                        "type": "string",
                        "description": "Category filter: company, news, research_paper, "
                        "pdf, github, tweet, personal_site, linkedin_profile",
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results (default: 5)",
                    },
                },
                "required": ["query"],
            },
        }

    async def execute(
        self,
        query: str,
        category: Optional[str] = None,
        num_results: int = 5,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute web search."""
        try:
            from super.core.search.exa import ExaCategory, ExaClient, ExaSearchType
        except ImportError:
            return ToolResult(
                success=False, error="Exa client not available - missing dependencies"
            )

        client = ExaClient(logger=logger)

        exa_category: Optional[ExaCategory] = None
        if category:
            category_lower = category.lower().replace("_", " ")
            for cat in ExaCategory:
                if cat.value == category_lower:
                    exa_category = cat
                    break

        try:
            response = await client.search(
                query=query,
                search_type=ExaSearchType.AUTO,
                category=exa_category,
                num_results=num_results,
                include_text=True,
                include_summary=True,
            )

            results: List[Dict[str, Any]] = []
            for result in response.results:
                results.append(
                    {
                        "id": result.id,
                        "title": result.title,
                        "url": result.url,
                        "summary": result.summary,
                        "source": _extract_source_from_url(result.url),
                        "published_date": result.published_date,
                        "author": result.author,
                        "score": result.score,
                    }
                )

            return ToolResult(
                success=True,
                data={
                    "results": results,
                    "count": len(results),
                    "query": query,
                    "search_type": response.search_type,
                },
            )

        except Exception as e:
            logger.error(f"Exa search error: {e}")
            return ToolResult(success=False, error=f"Search failed: {e}")


class ExaPeopleSearchTool(BaseTool):
    """
    Tool for searching people using Exa AI.

    Finds profiles on LinkedIn, Twitter, and personal sites.
    """

    name = "search_people"
    description = "Search for people on LinkedIn, Twitter, and personal sites"
    category = ToolCategory.SEARCH

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Person search query (name, role, company)",
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results (default: 5)",
                    },
                    "include_linkedin": {
                        "type": "boolean",
                        "description": "Include LinkedIn profiles (default: true)",
                    },
                    "include_twitter": {
                        "type": "boolean",
                        "description": "Include Twitter profiles (default: false)",
                    },
                },
                "required": ["query"],
            },
        }

    async def execute(
        self,
        query: str,
        num_results: int = 5,
        include_linkedin: bool = True,
        include_twitter: bool = False,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute people search."""
        try:
            from super.core.search.exa import ExaClient
        except ImportError:
            return ToolResult(
                success=False, error="Exa client not available - missing dependencies"
            )

        client = ExaClient(logger=logger)

        try:
            people = await client.search_people(
                query=query,
                num_results=num_results,
                include_linkedin=include_linkedin,
                include_twitter=include_twitter,
                include_personal_sites=True,
            )

            results: List[Dict[str, Any]] = []
            for person in people:
                results.append(
                    {
                        "id": person.id,
                        "name": person.name,
                        "title": person.title,
                        "company": person.company,
                        "bio": person.bio[:200] if person.bio else None,
                        "linkedin_url": person.linkedin_url,
                        "twitter_url": person.twitter_url,
                        "website": person.website,
                        "score": person.score,
                    }
                )

            return ToolResult(
                success=True,
                data={"people": results, "count": len(results), "query": query},
            )

        except Exception as e:
            logger.error(f"Exa people search error: {e}")
            return ToolResult(success=False, error=f"People search failed: {e}")
