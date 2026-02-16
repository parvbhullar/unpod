"""
SuperKik Schemas - Data structures for service discovery and booking.

This module defines Pydantic models and dataclasses for:
- Provider search and results
- Web search and people discovery cards
- Event/lead cards for discovery
- Booking requests and status
- Call status tracking
- User preferences
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class CallStatusType(str, Enum):
    """Call connection status."""

    IDLE = "idle"
    INITIATING = "initiating"
    CONNECTING = "connecting"
    RINGING = "ringing"
    ACTIVE = "active"
    ENDED = "ended"
    FAILED = "failed"


class BookingStatusType(str, Enum):
    """Booking request status."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProviderCard:
    """
    Provider card for display on frontend.

    Contains all information needed to render a provider recommendation card.
    """

    id: str
    name: str
    rating: float
    distance_km: float
    address: str
    phone: Optional[str] = None
    is_open: bool = True
    specialty: Optional[str] = None
    price_level: Optional[int] = None
    photo_url: Optional[str] = None
    opening_hours: Optional[List[str]] = None
    reviews_count: Optional[int] = None
    website: Optional[str] = None
    place_types: List[str] = field(default_factory=list)
    extra_info: Dict[str, Any] = field(default_factory=dict)  # Reservable, Delivery, etc.
    summary: Optional[str] = None  # editorialContent

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization with standard fields."""
        return {
            # Standard fields
            "id": self.id,
            "name": self.name,
            "description": self.specialty,  # Standard field
            "image": self.photo_url,  # Standard field
            "url": self.website,  # Standard field
            # Provider-specific fields
            "rating": self.rating,
            "distance_km": round(self.distance_km, 2),
            "address": self.address,
            "phone": self.phone,
            "is_open": self.is_open,
            "price_level": self.price_level,
            "opening_hours": self.opening_hours,
            "reviews_count": self.reviews_count,
            "place_types": self.place_types,
            "extra_info": self.extra_info,
            "summary": self.summary,
        }


@dataclass
class WebResultCard:
    """
    Card for displaying web search results.

    Used for Exa web search results with summaries.
    """

    id: str
    title: str
    url: str
    summary: Optional[str] = None
    source: Optional[str] = None
    published_date: Optional[str] = None
    author: Optional[str] = None
    image_url: Optional[str] = None
    score: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization with standard fields."""
        return {
            # Standard fields
            "id": self.id,
            "name": self.title,  # Standard field (maps from title)
            "description": self.summary,  # Standard field (maps from summary)
            "image": self.image_url,  # Standard field
            "url": self.url,  # Standard field
            # Web-specific fields
            "source": self.source,
            "published_date": self.published_date,
            "author": self.author,
            "score": self.score,
        }


@dataclass
class PersonCard:
    """
    Card for displaying people search results.

    Used for Exa people search with LinkedIn/Twitter profiles.
    """

    id: str
    name: str
    title: Optional[str] = None
    company: Optional[str] = None
    bio: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    website: Optional[str] = None
    image_url: Optional[str] = None
    score: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization with standard fields."""
        return {
            # Standard fields
            "id": self.id,
            "name": self.name,  # Standard field
            "description": self.bio,  # Standard field (maps from bio)
            "image": self.image_url,  # Standard field
            "url": self.linkedin_url
            or self.website,  # Standard field (prefer LinkedIn)
            # Person-specific fields
            "title": self.title,
            "company": self.company,
            "linkedin_url": self.linkedin_url,
            "twitter_url": self.twitter_url,
            "score": self.score,
        }


@dataclass
class EventCard:
    """
    Card for displaying events/leads.

    Used for discovery of events, conferences, meetups from web search.
    """

    id: str
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    source_url: Optional[str] = None
    event_date: Optional[str] = None
    location: Optional[str] = None
    organizer: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization with standard fields."""
        return {
            # Standard fields
            "id": self.id,
            "name": self.title,  # Standard field (maps from title)
            "description": self.description,  # Standard field
            "image": self.image_url,  # Standard field
            "url": self.source_url,  # Standard field (maps from source_url)
            # Event-specific fields
            "tags": self.tags,
            "event_date": self.event_date,
            "location": self.location,
            "organizer": self.organizer,
        }


@dataclass
class SearchRequest:
    """
    Parameters for provider search.

    Used to construct Google Places API queries.
    """

    query: str
    location: Optional[Tuple[float, float]] = None  # (lat, lng)
    radius_km: float = 5.0
    specialty: Optional[str] = None
    language: Optional[str] = "en"
    open_now: bool = False
    max_results: int = 10

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "location": self.location,
            "radius_km": self.radius_km,
            "specialty": self.specialty,
            "language": self.language,
            "open_now": self.open_now,
            "max_results": self.max_results,
        }


@dataclass
class SearchResult:
    """
    Result of a provider search.

    Contains the list of matching providers and search metadata.
    """

    providers: List[ProviderCard]
    query: str
    total_count: int
    search_location: Optional[Tuple[float, float]] = None
    radius_km: float = 5.0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "providers": [p.to_dict() for p in self.providers],
            "query": self.query,
            "total_count": self.total_count,
            "search_location": self.search_location,
            "radius_km": self.radius_km,
            "timestamp": self.timestamp,
        }


@dataclass
class BookingRequest:
    """
    Booking request data.

    Contains all information needed to create a booking.
    """

    provider_id: str
    provider_name: str
    provider_phone: Optional[str] = None
    requested_time: Optional[datetime] = None
    requested_time_str: Optional[str] = None  # Human-readable time
    service_type: Optional[str] = None
    notes: Optional[str] = None
    user_name: Optional[str] = None
    user_contact: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "provider_id": self.provider_id,
            "provider_name": self.provider_name,
            "provider_phone": self.provider_phone,
            "requested_time": self.requested_time.isoformat()
            if self.requested_time
            else None,
            "requested_time_str": self.requested_time_str,
            "service_type": self.service_type,
            "notes": self.notes,
            "user_name": self.user_name,
            "user_contact": self.user_contact,
        }


@dataclass
class BookingStatus:
    """
    Status of a booking request.

    Tracks the lifecycle of a booking from creation to completion.
    """

    booking_id: str
    status: BookingStatusType = BookingStatusType.PENDING
    request: Optional[BookingRequest] = None
    confirmation_code: Optional[str] = None
    confirmed_time: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization with standard fields."""
        provider_name = self.request.provider_name if self.request else None
        service_type = self.request.service_type if self.request else None
        return {
            # Standard fields
            "id": self.booking_id,  # Standard field (maps from booking_id)
            "name": provider_name,  # Standard field (from request)
            "description": service_type,  # Standard field (from request)
            # Booking-specific fields
            "status": self.status.value,
            "request": self.request.to_dict() if self.request else None,
            "confirmation_code": self.confirmation_code,
            "confirmed_time": self.confirmed_time.isoformat()
            if self.confirmed_time
            else None,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class CallStatus:
    """
    Status of a call connection.

    Tracks call lifecycle from initiation to completion.
    """

    call_id: str
    status: CallStatusType = CallStatusType.IDLE
    provider_id: Optional[str] = None
    provider_name: Optional[str] = None
    provider_phone: Optional[str] = None
    duration_seconds: int = 0
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization with standard fields."""
        # Generate description based on status
        status_descriptions = {
            CallStatusType.IDLE: "Call idle",
            CallStatusType.INITIATING: "Initiating call",
            CallStatusType.CONNECTING: "Connecting call",
            CallStatusType.RINGING: "Call ringing",
            CallStatusType.ACTIVE: "Call connected",
            CallStatusType.ENDED: "Call ended",
            CallStatusType.FAILED: "Call failed",
        }
        return {
            # Standard fields
            "id": self.call_id,  # Standard field (maps from call_id)
            "name": self.provider_name,  # Standard field
            "description": status_descriptions.get(self.status, "Unknown"),
            # Call-specific fields
            "status": self.status.value,
            "provider_id": self.provider_id,
            "provider_phone": self.provider_phone,
            "duration_seconds": self.duration_seconds,
            "error_message": self.error_message,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
        }


@dataclass
class CallContext:
    """Structured context gathered before initiating a call."""

    provider_id: str
    provider_name: str
    provider_phone: str

    # Information gathered for the call (generalized)
    main_objective: str = ""
    details: Dict[str, Any] = field(default_factory=dict)  # Key-value pairs for any details
    preferred_time: Optional[str] = None
    specific_questions: List[str] = field(default_factory=list)

    # Call configuration
    user_wants_direct_patch: bool = False
    language_preference: str = "english"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "provider_id": self.provider_id,
            "provider_name": self.provider_name,
            "provider_phone": self.provider_phone,
            "main_objective": self.main_objective,
            "details": self.details,
            "preferred_time": self.preferred_time,
            "specific_questions": self.specific_questions,
            "user_wants_direct_patch": self.user_wants_direct_patch,
            "language_preference": self.language_preference,
        }

    def is_ready_for_call(self) -> bool:
        """Check if minimum required info is gathered."""
        # Consider it ready if we have at least a main objective or a specific question
        return bool(self.main_objective or self.specific_questions)

    def build_instruction_set(self) -> str:
        """Generate structured instructions for callee conversation."""
        parts = [f"Goal: {self.main_objective or 'General inquiry'}"]
        if self.preferred_time:
            parts.append(f"Preferred time: {self.preferred_time}")
            
        for key, value in self.details.items():
            if key not in ["preferred_time"]:
                parts.append(f"{key.replace('_', ' ').title()}: {value}")
                
        if self.specific_questions:
            parts.append("Questions to ask:")
            for q in self.specific_questions:
                parts.append(f"- {q}")
        return "\n".join(parts)


@dataclass
class UserPreferences:
    """
    Stored user preferences for personalized results.

    Persisted across sessions to improve recommendations.
    """

    user_id: str
    preferred_language: Optional[str] = None
    preferred_specialty: Optional[str] = None
    preferred_distance_km: float = 5.0
    last_provider_id: Optional[str] = None
    last_provider_name: Optional[str] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "user_id": self.user_id,
            "preferred_language": self.preferred_language,
            "preferred_specialty": self.preferred_specialty,
            "preferred_distance_km": self.preferred_distance_km,
            "last_provider_id": self.last_provider_id,
            "last_provider_name": self.last_provider_name,
            "filters": self.filters,
            "history": self.history[-10:],  # Keep last 10 items
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def add_to_history(self, action: str, data: Dict[str, Any]) -> None:
        """Add an action to user history."""
        self.history.append(
            {
                "action": action,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        self.updated_at = datetime.utcnow().isoformat()

    def set_last_provider(self, provider_id: str, provider_name: str) -> None:
        """Update last used provider."""
        self.last_provider_id = provider_id
        self.last_provider_name = provider_name
        self.updated_at = datetime.utcnow().isoformat()


@dataclass
class SuperKikConfig:
    """
    SuperKik-specific configuration.

    Used to configure the SuperKik handler behavior.
    """

    google_places_api_key: Optional[str] = None
    default_search_radius_km: float = 5.0
    max_results: int = 10
    enable_preferences: bool = True
    preferences_ttl_days: int = 30
    enable_call_patching: bool = True
    enable_booking: bool = True
    default_location: Optional[Tuple[float, float]] = None  # Fallback location
    enable_orchestrator: bool = False  # Enable ThreeLayerOrchestrator for user mode

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SuperKikConfig":
        """Create config from dictionary."""
        superkik_data = data.get("superkik", {})
        return cls(
            google_places_api_key=superkik_data.get("google_places_api_key"),
            default_search_radius_km=superkik_data.get("default_search_radius_km", 5.0),
            max_results=superkik_data.get("max_results", 10),
            enable_preferences=superkik_data.get("enable_preferences", True),
            preferences_ttl_days=superkik_data.get("preferences_ttl_days", 30),
            enable_call_patching=superkik_data.get("enable_call_patching", True),
            enable_booking=superkik_data.get("enable_booking", True),
            default_location=superkik_data.get("default_location"),
            enable_orchestrator=superkik_data.get("enable_orchestrator", False),
        )
