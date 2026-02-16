"""
Exa Search Schemas - Data structures for Exa API responses.

Defines typed models for:
- Search results (web, people)
- Research tasks and status
- API response structures
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ExaSearchType(str, Enum):
    """Exa search type options."""

    NEURAL = "neural"
    FAST = "fast"
    AUTO = "auto"
    DEEP = "deep"


class ExaCategory(str, Enum):
    """Exa content category filters."""

    COMPANY = "company"
    RESEARCH_PAPER = "research paper"
    NEWS = "news"
    PDF = "pdf"
    GITHUB = "github"
    TWEET = "tweet"
    PERSONAL_SITE = "personal site"
    LINKEDIN_PROFILE = "linkedin profile"
    FINANCIAL_REPORT = "financial report"
    PEOPLE = "people"


class ResearchStatus(str, Enum):
    """Research task status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class ExaResult:
    """
    Single search result from Exa API.

    Represents a web page or document returned from search.
    """

    id: str
    url: str
    title: str
    score: float = 0.0
    published_date: Optional[str] = None
    author: Optional[str] = None
    text: Optional[str] = None
    summary: Optional[str] = None
    highlights: List[str] = field(default_factory=list)
    highlight_scores: List[float] = field(default_factory=list)
    image: Optional[str] = None
    favicon: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "score": self.score,
            "published_date": self.published_date,
            "author": self.author,
            "text": self.text[:500] if self.text else None,
            "summary": self.summary,
            "highlights": self.highlights,
            "image": self.image,
        }

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "ExaResult":
        """Create from Exa API response."""
        return cls(
            id=data.get("id", ""),
            url=data.get("url", ""),
            title=data.get("title", ""),
            score=data.get("score", 0.0),
            published_date=data.get("publishedDate"),
            author=data.get("author"),
            text=data.get("text"),
            summary=data.get("summary"),
            highlights=data.get("highlights", []),
            highlight_scores=data.get("highlightScores", []),
            image=data.get("image"),
            favicon=data.get("favicon"),
        )


@dataclass
class PersonResult:
    """
    Person search result from Exa API.

    Contains information about a person found via search.
    """

    id: str
    name: str
    url: str
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    website: Optional[str] = None
    image_url: Optional[str] = None
    score: float = 0.0
    source_type: str = "web"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "bio": self.bio[:300] if self.bio else None,
            "linkedin_url": self.linkedin_url,
            "twitter_url": self.twitter_url,
            "website": self.website,
            "image_url": self.image_url,
            "score": self.score,
        }

    @classmethod
    def from_exa_result(cls, result: ExaResult) -> "PersonResult":
        """Create PersonResult from ExaResult with heuristic parsing."""
        name = result.title
        title = None
        company = None
        linkedin_url = None
        twitter_url = None
        website = None

        url_lower = result.url.lower()
        if "linkedin.com" in url_lower:
            linkedin_url = result.url
            source_type = "linkedin"
        elif "twitter.com" in url_lower or "x.com" in url_lower:
            twitter_url = result.url
            source_type = "twitter"
        else:
            website = result.url
            source_type = "web"

        if result.summary:
            parts = result.summary.split(" at ")
            if len(parts) >= 2:
                title = parts[0].strip()
                company = parts[1].split(".")[0].strip() if parts[1] else None

        bio = result.summary or result.text

        return cls(
            id=result.id,
            name=name,
            url=result.url,
            title=title,
            company=company,
            bio=bio,
            linkedin_url=linkedin_url,
            twitter_url=twitter_url,
            website=website,
            image_url=result.image,
            score=result.score,
            source_type=source_type,
        )


@dataclass
class ExaSearchResponse:
    """
    Complete search response from Exa API.

    Contains results and metadata about the search.
    """

    request_id: str
    results: List[ExaResult]
    search_type: str = "auto"
    cost_dollars: Optional[float] = None
    query: str = ""
    total_count: int = 0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "request_id": self.request_id,
            "results": [r.to_dict() for r in self.results],
            "search_type": self.search_type,
            "cost_dollars": self.cost_dollars,
            "query": self.query,
            "total_count": self.total_count,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_api_response(
        cls, data: Dict[str, Any], query: str = ""
    ) -> "ExaSearchResponse":
        """Create from Exa API response."""
        results = [ExaResult.from_api_response(r) for r in data.get("results", [])]
        return cls(
            request_id=data.get("requestId", ""),
            results=results,
            search_type=data.get("searchType", "auto"),
            cost_dollars=data.get("costDollars", {}).get("total"),
            query=query,
            total_count=len(results),
        )


@dataclass
class ResearchEvent:
    """A single event in research task execution."""

    event_type: str
    timestamp: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class ResearchTask:
    """
    Async research task from Exa Research API.

    Represents a long-running research task.
    """

    research_id: str
    status: ResearchStatus
    instructions: str
    model: str = "exa-research"
    created_at: Optional[str] = None
    finished_at: Optional[str] = None
    output_content: Optional[str] = None
    output_parsed: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    cost_dollars: Optional[float] = None
    events: List[ResearchEvent] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "research_id": self.research_id,
            "status": self.status.value,
            "instructions": self.instructions[:200] + "..."
            if len(self.instructions) > 200
            else self.instructions,
            "model": self.model,
            "created_at": self.created_at,
            "finished_at": self.finished_at,
            "output_content": self.output_content[:500] if self.output_content else None,
            "output_parsed": self.output_parsed,
            "error_message": self.error_message,
            "cost_dollars": self.cost_dollars,
        }

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "ResearchTask":
        """Create from Exa Research API response."""
        output = data.get("output", {})
        events_data = data.get("events", [])
        events = [
            ResearchEvent(
                event_type=e.get("type", ""),
                timestamp=e.get("timestamp", ""),
                details=e.get("details"),
            )
            for e in events_data
        ]

        status_str = data.get("status", "pending").lower()
        status = ResearchStatus(status_str) if status_str in [
            s.value for s in ResearchStatus
        ] else ResearchStatus.PENDING

        return cls(
            research_id=data.get("researchId", ""),
            status=status,
            instructions=data.get("instructions", ""),
            model=data.get("model", "exa-research"),
            created_at=data.get("createdAt"),
            finished_at=data.get("finishedAt"),
            output_content=output.get("content") if isinstance(output, dict) else None,
            output_parsed=output.get("parsed") if isinstance(output, dict) else None,
            error_message=data.get("error"),
            cost_dollars=data.get("costDollars", {}).get("total")
            if isinstance(data.get("costDollars"), dict)
            else None,
            events=events,
        )

    @property
    def is_complete(self) -> bool:
        """Check if research task is complete."""
        return self.status in (
            ResearchStatus.COMPLETED,
            ResearchStatus.CANCELLED,
            ResearchStatus.FAILED,
        )

    @property
    def is_successful(self) -> bool:
        """Check if research completed successfully."""
        return self.status == ResearchStatus.COMPLETED
