"""
Exa Tool Plugin - Web search and people discovery for SuperKik.

Provides tools for:
- Web search with semantic understanding
- People search (LinkedIn, social profiles)
- Async research tasks

Uses Exa AI's search and research APIs.
"""

import json
from typing import TYPE_CHECKING, Annotated, Any, Callable, Dict, List, Optional

from pydantic import Field

from super.core.logging import logging as app_logging
from super.core.search.exa import (
    ExaCategory,
    ExaClient,
    ExaSearchType,
    ResearchStatus,
)
from super.core.voice.superkik.schema import PersonCard, WebResultCard
from super.core.voice.superkik.tools.base import ToolPlugin

if TYPE_CHECKING:
    from super.core.voice.superkik.handler import SuperKikHandler

logger = app_logging.get_logger("superkik.tools.exa")


def _extract_source_from_url(url: str) -> Optional[str]:
    """Extract domain name from URL for source attribution."""
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        domain = parsed.netloc
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return None


async def search_web_impl(
    handler: "SuperKikHandler",
    query: str,
    category: Optional[str] = None,
    num_results: int = 5,
    include_summary: bool = True,
) -> Dict[str, Any]:
    """
    Implementation of web search using Exa.

    Args:
        handler: SuperKikHandler instance
        query: Search query
        category: Optional category filter
        num_results: Number of results
        include_summary: Include AI summaries

    Returns:
        Dict with search results and publishes WebResultCards
    """
    client = ExaClient(logger=logger)

    exa_category: Optional[ExaCategory] = None
    if category:
        category_lower = category.lower().replace("_", " ")
        for cat in ExaCategory:
            if cat.value == category_lower:
                exa_category = cat
                break

    response = await client.search(
        query=query,
        search_type=ExaSearchType.AUTO,
        category=exa_category,
        num_results=num_results,
        include_text=True,
        include_summary=include_summary,
    )

    results = []
    web_cards: List[WebResultCard] = []

    for result in response.results:
        results.append(
            {
                "id": result.id,
                "title": result.title,
                "url": result.url,
                "summary": result.summary,
                "published_date": result.published_date,
                "author": result.author,
                "score": result.score,
            }
        )

        web_cards.append(
            WebResultCard(
                id=result.id,
                title=result.title or "Untitled",
                url=result.url,
                summary=result.summary,
                source=_extract_source_from_url(result.url),
                published_date=result.published_date,
                author=result.author,
                image_url=getattr(result, "image_url", None),
                score=result.score,
            )
        )

    if handler._event_bridge and web_cards:
        await handler._publish_web_results(web_cards, query)

    return {
        "query": query,
        "count": len(results),
        "results": results,
        "search_type": response.search_type,
    }


async def search_people_impl(
    handler: "SuperKikHandler",
    query: str,
    num_results: int = 5,
    include_linkedin: bool = True,
    include_twitter: bool = False,
) -> Dict[str, Any]:
    """
    Implementation of people search using Exa.

    Args:
        handler: SuperKikHandler instance
        query: Person search query
        num_results: Number of results
        include_linkedin: Include LinkedIn profiles
        include_twitter: Include Twitter profiles

    Returns:
        Dict with people results and publishes PersonCards
    """
    client = ExaClient(logger=logger)

    people = await client.search_people(
        query=query,
        num_results=num_results,
        include_linkedin=include_linkedin,
        include_twitter=include_twitter,
        include_personal_sites=True,
    )

    results = []
    person_cards: List[PersonCard] = []

    for person in people:
        bio_truncated = person.bio[:200] if person.bio else None

        results.append(
            {
                "id": person.id,
                "name": person.name,
                "title": person.title,
                "company": person.company,
                "bio": bio_truncated,
                "linkedin_url": person.linkedin_url,
                "twitter_url": person.twitter_url,
                "website": person.website,
                "score": person.score,
            }
        )

        person_cards.append(
            PersonCard(
                id=person.id,
                name=person.name or "Unknown",
                title=person.title,
                company=person.company,
                bio=bio_truncated,
                linkedin_url=person.linkedin_url,
                twitter_url=person.twitter_url,
                website=person.website,
                image_url=getattr(person, "image_url", None),
                score=person.score,
            )
        )

    if handler._event_bridge and person_cards:
        await handler._publish_people_results(person_cards, query)

    return {
        "query": query,
        "count": len(results),
        "people": results,
    }


async def create_research_impl(
    handler: "SuperKikHandler",
    instructions: str,
    model: str = "exa-research",
) -> Dict[str, Any]:
    """
    Implementation of research task creation using Exa.

    Args:
        handler: SuperKikHandler instance
        instructions: Research instructions
        model: Research model (fast, standard, pro)

    Returns:
        Dict with research task info
    """
    client = ExaClient(logger=logger)

    model_map = {
        "fast": "exa-research-fast",
        "standard": "exa-research",
        "pro": "exa-research-pro",
    }
    exa_model = model_map.get(model.lower(), "exa-research")

    task = await client.create_research(
        instructions=instructions,
        model=exa_model,
    )

    return {
        "research_id": task.research_id,
        "status": task.status.value,
        "model": task.model,
        "created_at": task.created_at,
        "message": f"Research task created. ID: {task.research_id}",
    }


async def get_research_impl(
    handler: "SuperKikHandler",
    research_id: str,
) -> Dict[str, Any]:
    """
    Implementation of research status check using Exa.

    Args:
        handler: SuperKikHandler instance
        research_id: Research task ID

    Returns:
        Dict with research status and output
    """
    client = ExaClient(logger=logger)

    task = await client.get_research(research_id)

    result: Dict[str, Any] = {
        "research_id": task.research_id,
        "status": task.status.value,
        "is_complete": task.is_complete,
    }

    if task.is_successful:
        result["output"] = task.output_content[:2000] if task.output_content else None
        result["cost_dollars"] = task.cost_dollars
    elif task.status == ResearchStatus.FAILED:
        result["error"] = task.error_message

    return result


class ExaToolPlugin(ToolPlugin):
    """
    Tool plugin for Exa search and research.

    Provides tools:
    - search_web: Search the web with semantic understanding
    - search_people: Find people on LinkedIn, Twitter, etc.
    - create_research: Start an async research task
    - get_research: Check research task status
    """

    name = "exa"

    def _create_tools(self) -> List[Callable]:
        """Create Exa-related tool functions."""
        tools = [
            self._create_search_web_tool(),
            self._create_search_people_tool(),
        ]

        if self.options.get("enable_research", True):
            tools.extend(
                [
                    self._create_research_tool(),
                    self._create_get_research_tool(),
                ]
            )

        return tools

    def _create_search_web_tool(self) -> Callable:
        """Create the search_web function tool."""
        try:
            from livekit.agents.llm import function_tool
        except ImportError:
            self._logger.warning("livekit.agents not available")
            return lambda: None

        handler = self._handler

        @function_tool
        async def search_web(
            query: Annotated[
                str,
                Field(description="Search query in natural language"),
            ],
            category: Annotated[
                Optional[str],
                Field(
                    description="Category filter: company, news, research_paper, "
                    "pdf, github, tweet, personal_site, linkedin_profile, financial_report"
                ),
            ] = None,
        ) -> str:
            """
            Search the web using Exa's semantic search.

            Use this tool when the user asks for information about:
            - Companies, news, research papers
            - GitHub repositories, tweets
            - Financial reports, technical documents

            Returns a list of relevant web results with summaries.
            """
            try:
                num_results = self.options.get("max_results", 5)
                result = await search_web_impl(
                    handler=handler,
                    query=query,
                    category=category,
                    num_results=num_results,
                    include_summary=True,
                )

                if not result["results"]:
                    return json.dumps(
                        {
                            "status": "no_results",
                            "message": f"No results found for '{query}'",
                        }
                    )

                return json.dumps(
                    {
                        "status": "success",
                        "query": query,
                        "count": result["count"],
                        "results": result["results"],
                        "message": f"Found {result['count']} results. Cards displayed to user.",
                    }
                )

            except Exception as e:
                self._logger.error(f"search_web error: {e}")
                return json.dumps(
                    {
                        "status": "error",
                        "message": f"Search error: {str(e)}",
                    }
                )

        return search_web

    def _create_search_people_tool(self) -> Callable:
        """Create the search_people function tool."""
        try:
            from livekit.agents.llm import function_tool
        except ImportError:
            self._logger.warning("livekit.agents not available")
            return lambda: None

        handler = self._handler

        @function_tool
        async def search_people(
            query: Annotated[
                str,
                Field(
                    description="Person search query (name, role, company). "
                    "Examples: 'CEO of Tesla', 'John Smith software engineer'"
                ),
            ],
            include_linkedin: Annotated[
                bool,
                Field(description="Include LinkedIn profiles in results"),
            ] = True,
        ) -> str:
            """
            Search for people using Exa's people search.

            Use this tool when the user asks to find:
            - Specific individuals by name
            - People by role (CEO, CTO, engineer)
            - People at specific companies
            - Professional profiles and contact info

            Returns profiles with LinkedIn, Twitter, and website links.
            """
            try:
                num_results = self.options.get("max_results", 5)
                result = await search_people_impl(
                    handler=handler,
                    query=query,
                    num_results=num_results,
                    include_linkedin=include_linkedin,
                    include_twitter=self.options.get("include_twitter", True),
                )

                if not result["people"]:
                    return json.dumps(
                        {
                            "status": "no_results",
                            "message": f"No people found for '{query}'",
                        }
                    )

                return json.dumps(
                    {
                        "status": "success",
                        "query": query,
                        "count": result["count"],
                        "people": result["people"],
                        "message": f"Found {result['count']} people. Cards displayed to user.",
                    }
                )

            except Exception as e:
                self._logger.error(f"search_people error: {e}")
                return json.dumps(
                    {
                        "status": "error",
                        "message": f"People search error: {str(e)}",
                    }
                )

        return search_people

    def _create_research_tool(self) -> Callable:
        """Create the create_research function tool."""
        try:
            from livekit.agents.llm import function_tool
        except ImportError:
            self._logger.warning("livekit.agents not available")
            return lambda: None

        handler = self._handler

        @function_tool
        async def create_research(
            instructions: Annotated[
                str,
                Field(
                    description="Research instructions describing what to investigate. "
                    "Be specific about the topic, questions to answer, and output format."
                ),
            ],
            model: Annotated[
                str,
                Field(description="Research model: fast, standard, or pro"),
            ] = "standard",
        ) -> str:
            """
            Start an async research task using Exa Research API.

            Use this tool for complex research that requires:
            - Multiple sources and synthesis
            - In-depth analysis
            - Structured reports

            Returns a research_id to check status with get_research.
            """
            try:
                result = await create_research_impl(
                    handler=handler,
                    instructions=instructions,
                    model=model,
                )

                return json.dumps(
                    {
                        "status": "success",
                        "research_id": result["research_id"],
                        "model": result["model"],
                        "message": "Research task started. Use get_research to check status.",
                    }
                )

            except Exception as e:
                self._logger.error(f"create_research error: {e}")
                return json.dumps(
                    {
                        "status": "error",
                        "message": f"Research creation error: {str(e)}",
                    }
                )

        return create_research

    def _create_get_research_tool(self) -> Callable:
        """Create the get_research function tool."""
        try:
            from livekit.agents.llm import function_tool
        except ImportError:
            self._logger.warning("livekit.agents not available")
            return lambda: None

        handler = self._handler

        @function_tool
        async def get_research(
            research_id: Annotated[
                str,
                Field(description="Research task ID from create_research"),
            ],
        ) -> str:
            """
            Check status of a research task.

            Returns the current status and output if complete.
            """
            try:
                result = await get_research_impl(
                    handler=handler,
                    research_id=research_id,
                )

                if result["is_complete"]:
                    if result["status"] == "completed":
                        return json.dumps(
                            {
                                "status": "success",
                                "research_status": "completed",
                                "output": result.get("output"),
                            }
                        )
                    else:
                        return json.dumps(
                            {
                                "status": "failed",
                                "error": result.get("error", "Research failed"),
                            }
                        )

                return json.dumps(
                    {
                        "status": "pending",
                        "research_status": result["status"],
                        "message": "Research is still in progress. Check again later.",
                    }
                )

            except Exception as e:
                self._logger.error(f"get_research error: {e}")
                return json.dumps(
                    {
                        "status": "error",
                        "message": f"Get research error: {str(e)}",
                    }
                )

        return get_research

    def get_metrics(self) -> Optional[Dict[str, Any]]:
        """Return Exa usage metrics."""
        return {
            "enabled": self.enabled,
            "tools": self.get_tool_names(),
        }
