"""
Exa Search Client - Core search functionality using Exa AI.

Provides a unified client for:
- Web search with semantic understanding
- People search (LinkedIn, social profiles)
- Async research tasks

Usage:
    from super.core.search.exa import ExaClient

    client = ExaClient()
    results = await client.search("AI startups in NYC")
    people = await client.search_people("CTO at Anthropic")
"""

from super.core.search.exa.client import ExaClient
from super.core.search.exa.schema import (
    ExaCategory,
    ExaResult,
    ExaSearchResponse,
    ExaSearchType,
    PersonResult,
    ResearchStatus,
    ResearchTask,
)

__all__ = [
    "ExaClient",
    "ExaCategory",
    "ExaResult",
    "ExaSearchResponse",
    "ExaSearchType",
    "PersonResult",
    "ResearchStatus",
    "ResearchTask",
]
