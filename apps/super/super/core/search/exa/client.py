"""
Exa Search Client - HTTP client for Exa AI APIs.

Provides async methods for:
- search: Web search with semantic understanding
- search_people: Find people (LinkedIn, social profiles)
- create_research: Start async research task
- get_research: Poll research task status
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

import httpx

from super.core.search.exa.schema import (
    ExaCategory,
    ExaResult,
    ExaSearchResponse,
    ExaSearchType,
    PersonResult,
    ResearchStatus,
    ResearchTask,
)

EXA_API_BASE_URL = "https://api.exa.ai"
EXA_SEARCH_ENDPOINT = f"{EXA_API_BASE_URL}/search"
EXA_RESEARCH_ENDPOINT = f"{EXA_API_BASE_URL}/research/v1"

DEFAULT_TIMEOUT = 30.0
RESEARCH_POLL_INTERVAL = 2.0
RESEARCH_MAX_WAIT = 300.0


class ExaClient:
    """
    Async client for Exa AI search and research APIs.

    Example:
        client = ExaClient()
        results = await client.search("AI companies", category="company")
        people = await client.search_people("CTO of OpenAI")
        task = await client.create_research("Analyze AI trends 2025")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        logger: Optional[logging.Logger] = None,
    ):
        self._api_key = api_key or os.getenv("EXA_API_KEY", "")
        self._timeout = timeout
        self._logger = logger or logging.getLogger("exa.client")

        if not self._api_key:
            self._logger.warning("EXA_API_KEY not set")

    @property
    def api_key(self) -> str:
        """Get API key."""
        return self._api_key

    def _get_headers(self) -> Dict[str, str]:
        """Build request headers."""
        return {
            "Content-Type": "application/json",
            "x-api-key": self._api_key,
        }

    async def search(
        self,
        query: str,
        search_type: ExaSearchType = ExaSearchType.AUTO,
        category: Optional[ExaCategory] = None,
        num_results: int = 10,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        start_published_date: Optional[str] = None,
        end_published_date: Optional[str] = None,
        include_text: bool = True,
        include_summary: bool = True,
        include_highlights: bool = False,
        livecrawl: str = "fallback",
    ) -> ExaSearchResponse:
        """
        Search the web using Exa's semantic search.

        Args:
            query: Search query (natural language)
            search_type: neural, fast, auto, or deep
            category: Filter by content category
            num_results: Number of results (1-100)
            include_domains: Only search these domains
            exclude_domains: Exclude these domains
            start_published_date: ISO 8601 date filter
            end_published_date: ISO 8601 date filter
            include_text: Include full page text
            include_summary: Include AI-generated summary
            include_highlights: Include relevant snippets
            livecrawl: never, fallback, preferred, always

        Returns:
            ExaSearchResponse with results
        """
        if not self._api_key:
            self._logger.warning("No API key, returning empty response")
            return ExaSearchResponse(
                request_id="no_api_key",
                results=[],
                query=query,
            )

        body: Dict[str, Any] = {
            "query": query,
            "type": search_type.value,
            "numResults": min(num_results, 100),
        }

        if category:
            body["category"] = category.value

        if include_domains:
            body["includeDomains"] = include_domains[:1200]

        if exclude_domains:
            body["excludeDomains"] = exclude_domains[:1200]

        if start_published_date:
            body["startPublishedDate"] = start_published_date

        if end_published_date:
            body["endPublishedDate"] = end_published_date

        contents: Dict[str, Any] = {"livecrawl": livecrawl}
        if include_text:
            contents["text"] = {"maxCharacters": 5000}
        if include_summary:
            contents["summary"] = True
        if include_highlights:
            contents["highlights"] = {"numSentences": 3, "highlightsPerUrl": 3}

        body["contents"] = contents

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    EXA_SEARCH_ENDPOINT,
                    headers=self._get_headers(),
                    json=body,
                )
                response.raise_for_status()
                data = response.json()

                return ExaSearchResponse.from_api_response(data, query)

        except httpx.HTTPStatusError as e:
            self._logger.error(
                f"Exa API error: {e.response.status_code} - {e.response.text}"
            )
            return ExaSearchResponse(
                request_id="error",
                results=[],
                query=query,
            )
        except Exception as e:
            self._logger.error(f"Exa search error: {e}")
            return ExaSearchResponse(
                request_id="error",
                results=[],
                query=query,
            )

    async def search_people(
        self,
        query: str,
        num_results: int = 10,
        include_linkedin: bool = True,
        include_twitter: bool = True,
        include_personal_sites: bool = True,
    ) -> List[PersonResult]:
        """
        Search for people using Exa's people search.

        Uses category="people" and optionally includes LinkedIn, Twitter,
        and personal site searches.

        Args:
            query: Person search query (name, role, company)
            num_results: Number of results
            include_linkedin: Include LinkedIn profiles
            include_twitter: Include Twitter/X profiles
            include_personal_sites: Include personal websites

        Returns:
            List of PersonResult objects
        """
        include_domains: List[str] = []
        if include_linkedin:
            include_domains.append("linkedin.com")
        if include_twitter:
            include_domains.extend(["twitter.com", "x.com"])

        response = await self.search(
            query=query,
            search_type=ExaSearchType.AUTO,
            category=ExaCategory.PEOPLE,
            num_results=num_results,
            include_domains=include_domains if include_domains else None,
            include_text=True,
            include_summary=True,
        )

        people: List[PersonResult] = []
        for result in response.results:
            person = PersonResult.from_exa_result(result)
            people.append(person)

        if include_personal_sites and len(people) < num_results:
            personal_response = await self.search(
                query=query,
                search_type=ExaSearchType.AUTO,
                category=ExaCategory.PERSONAL_SITE,
                num_results=num_results - len(people),
                include_text=True,
                include_summary=True,
            )
            for result in personal_response.results:
                person = PersonResult.from_exa_result(result)
                people.append(person)

        return people[:num_results]

    async def create_research(
        self,
        instructions: str,
        model: str = "exa-research",
        output_schema: Optional[Dict[str, Any]] = None,
    ) -> ResearchTask:
        """
        Create an async research task.

        Starts a long-running research task that gathers and synthesizes
        information based on instructions.

        Args:
            instructions: Research instructions (max 4096 chars)
            model: exa-research-fast, exa-research, or exa-research-pro
            output_schema: Optional JSON schema for structured output

        Returns:
            ResearchTask with research_id for polling
        """
        if not self._api_key:
            self._logger.warning("No API key for research")
            return ResearchTask(
                research_id="no_api_key",
                status=ResearchStatus.FAILED,
                instructions=instructions,
                error_message="EXA_API_KEY not set",
            )

        body: Dict[str, Any] = {
            "instructions": instructions[:4096],
            "model": model,
        }

        if output_schema:
            body["outputSchema"] = output_schema

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    EXA_RESEARCH_ENDPOINT,
                    headers=self._get_headers(),
                    json=body,
                )
                response.raise_for_status()
                data = response.json()

                return ResearchTask.from_api_response(data)

        except httpx.HTTPStatusError as e:
            self._logger.error(
                f"Exa research API error: {e.response.status_code} - {e.response.text}"
            )
            return ResearchTask(
                research_id="error",
                status=ResearchStatus.FAILED,
                instructions=instructions,
                error_message=str(e),
            )
        except Exception as e:
            self._logger.error(f"Exa research error: {e}")
            return ResearchTask(
                research_id="error",
                status=ResearchStatus.FAILED,
                instructions=instructions,
                error_message=str(e),
            )

    async def get_research(self, research_id: str) -> ResearchTask:
        """
        Get research task status and results.

        Poll this endpoint to check if research is complete.

        Args:
            research_id: ID from create_research

        Returns:
            ResearchTask with current status and output if complete
        """
        if not self._api_key:
            return ResearchTask(
                research_id=research_id,
                status=ResearchStatus.FAILED,
                instructions="",
                error_message="EXA_API_KEY not set",
            )

        url = f"{EXA_RESEARCH_ENDPOINT}/{research_id}"

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()

                return ResearchTask.from_api_response(data)

        except Exception as e:
            self._logger.error(f"Exa get_research error: {e}")
            return ResearchTask(
                research_id=research_id,
                status=ResearchStatus.FAILED,
                instructions="",
                error_message=str(e),
            )

    async def research_and_wait(
        self,
        instructions: str,
        model: str = "exa-research",
        output_schema: Optional[Dict[str, Any]] = None,
        max_wait_seconds: float = RESEARCH_MAX_WAIT,
        poll_interval: float = RESEARCH_POLL_INTERVAL,
    ) -> ResearchTask:
        """
        Create research task and wait for completion.

        Convenience method that polls until research completes or times out.

        Args:
            instructions: Research instructions
            model: Research model to use
            output_schema: Optional JSON schema
            max_wait_seconds: Maximum wait time
            poll_interval: Seconds between polls

        Returns:
            Completed ResearchTask
        """
        task = await self.create_research(instructions, model, output_schema)

        if task.status == ResearchStatus.FAILED:
            return task

        elapsed = 0.0
        while elapsed < max_wait_seconds and not task.is_complete:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            task = await self.get_research(task.research_id)

        if not task.is_complete:
            task.status = ResearchStatus.FAILED
            task.error_message = f"Research timed out after {max_wait_seconds}s"

        return task
