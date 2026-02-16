"""
Places Tool Plugin - Provider discovery for SuperKik.

Provides tools for searching and retrieving provider information
using the Google Places API (New):
- Text Search API for text-based queries
- Nearby Search API for location-based discovery

Reference:
- https://developers.google.com/maps/documentation/places/web-service/text-search
- https://developers.google.com/maps/documentation/places/web-service/nearby-search
- https://developers.google.com/maps/documentation/places/web-service/place-types
"""

import json
import os
import uuid
from enum import Enum
from math import atan2, cos, radians, sin, sqrt
from typing import TYPE_CHECKING, Annotated, Any, Callable, Dict, List, Optional, Tuple

from pydantic import Field

from super.core.logging import logging as app_logging
from super.core.context.schema import Event, Message
from super.core.voice.superkik.schema import ProviderCard, SearchResult
from super.core.voice.superkik.tools.base import ToolPlugin

if TYPE_CHECKING:
    from super.core.voice.superkik.handler import SuperKikHandler

logger = app_logging.get_logger("superkik.tools.places")

# Action topic for requesting user actions from UI
TOPIC_USER_ACTION = "user_action"

# Google Places API configuration
GOOGLE_PLACES_API_KEY = os.getenv("GEMINI_API_KEY", "")
GOOGLE_PLACES_BASE_URL = "https://places.googleapis.com/v1/places"

# Debug mode: When enabled, replaces all place phone numbers with test number
# Set PLACES_DEBUG_MODE=true to enable for testing real-time calling
PLACES_DEBUG_MODE = os.getenv("PLACES_DEBUG_MODE", "false").lower() == "true"
PLACES_DEBUG_PHONE = os.getenv("PLACES_DEBUG_PHONE", "+919738301026")

if PLACES_DEBUG_MODE:
    logger.warning(
        f"[PLACES] Debug mode ENABLED - all phone numbers will be replaced with {PLACES_DEBUG_PHONE}"
    )


class PlaceTypeCategory(str, Enum):
    """Categories of place types for filtering."""

    HEALTH = "health"
    FOOD = "food"
    SERVICES = "services"
    SHOPPING = "shopping"
    ENTERTAINMENT = "entertainment"
    LODGING = "lodging"
    TRANSPORTATION = "transportation"
    AUTOMOTIVE = "automotive"
    FINANCE = "finance"
    EDUCATION = "education"
    SPORTS = "sports"
    GOVERNMENT = "government"


# Place types from Google Places API Table A (can be used for filtering)
# Reference: https://developers.google.com/maps/documentation/places/web-service/place-types
PLACE_TYPES: Dict[PlaceTypeCategory, List[str]] = {
    PlaceTypeCategory.HEALTH: [
        "chiropractor",
        "dental_clinic",
        "dentist",
        "doctor",
        "drugstore",
        "hospital",
        "massage",
        "medical_lab",
        "pharmacy",
        "physiotherapist",
        "sauna",
        "skin_care_clinic",
        "spa",
        "tanning_studio",
        "wellness_center",
        "yoga_studio",
    ],
    PlaceTypeCategory.FOOD: [
        "american_restaurant",
        "bakery",
        "bar",
        "barbecue_restaurant",
        "brazilian_restaurant",
        "breakfast_restaurant",
        "brunch_restaurant",
        "cafe",
        "chinese_restaurant",
        "coffee_shop",
        "fast_food_restaurant",
        "french_restaurant",
        "greek_restaurant",
        "hamburger_restaurant",
        "ice_cream_shop",
        "indian_restaurant",
        "indonesian_restaurant",
        "italian_restaurant",
        "japanese_restaurant",
        "korean_restaurant",
        "lebanese_restaurant",
        "meal_delivery",
        "meal_takeaway",
        "mediterranean_restaurant",
        "mexican_restaurant",
        "middle_eastern_restaurant",
        "pizza_restaurant",
        "ramen_restaurant",
        "restaurant",
        "sandwich_shop",
        "seafood_restaurant",
        "spanish_restaurant",
        "steak_house",
        "sushi_restaurant",
        "thai_restaurant",
        "turkish_restaurant",
        "vegan_restaurant",
        "vegetarian_restaurant",
        "vietnamese_restaurant",
    ],
    PlaceTypeCategory.SERVICES: [
        "barber_shop",
        "beauty_salon",
        "electrician",
        "florist",
        "hair_care",
        "hair_salon",
        "laundry",
        "locksmith",
        "moving_company",
        "painter",
        "plumber",
        "real_estate_agency",
        "roofing_contractor",
        "storage",
        "tailor",
        "telecommunications_service_provider",
        "travel_agency",
        "veterinary_care",
    ],
    PlaceTypeCategory.SHOPPING: [
        "auto_parts_store",
        "bicycle_store",
        "book_store",
        "cell_phone_store",
        "clothing_store",
        "convenience_store",
        "department_store",
        "discount_store",
        "electronics_store",
        "furniture_store",
        "gift_shop",
        "grocery_store",
        "hardware_store",
        "home_goods_store",
        "home_improvement_store",
        "jewelry_store",
        "liquor_store",
        "market",
        "pet_store",
        "shoe_store",
        "shopping_mall",
        "sporting_goods_store",
        "store",
        "supermarket",
        "wholesaler",
    ],
    PlaceTypeCategory.ENTERTAINMENT: [
        "amusement_center",
        "amusement_park",
        "aquarium",
        "art_gallery",
        "bowling_alley",
        "casino",
        "comedy_club",
        "concert_hall",
        "cultural_center",
        "event_venue",
        "movie_theater",
        "museum",
        "night_club",
        "opera_house",
        "park",
        "performing_arts_theater",
        "tourist_attraction",
        "video_arcade",
        "visitor_center",
        "zoo",
    ],
    PlaceTypeCategory.LODGING: [
        "bed_and_breakfast",
        "campground",
        "cottage",
        "extended_stay_hotel",
        "farmstay",
        "guest_house",
        "hostel",
        "hotel",
        "inn",
        "lodging",
        "motel",
        "resort_hotel",
        "rv_park",
    ],
    PlaceTypeCategory.TRANSPORTATION: [
        "airport",
        "bus_station",
        "bus_stop",
        "ferry_terminal",
        "light_rail_station",
        "park_and_ride",
        "subway_station",
        "taxi_stand",
        "train_station",
        "transit_station",
    ],
    PlaceTypeCategory.AUTOMOTIVE: [
        "car_dealer",
        "car_rental",
        "car_repair",
        "car_wash",
        "electric_vehicle_charging_station",
        "gas_station",
        "parking",
        "rest_stop",
    ],
    PlaceTypeCategory.FINANCE: [
        "accounting",
        "atm",
        "bank",
    ],
    PlaceTypeCategory.EDUCATION: [
        "library",
        "preschool",
        "primary_school",
        "school",
        "secondary_school",
        "university",
    ],
    PlaceTypeCategory.SPORTS: [
        "athletic_field",
        "fitness_center",
        "golf_course",
        "gym",
        "ice_skating_rink",
        "playground",
        "ski_resort",
        "sports_club",
        "sports_complex",
        "stadium",
        "swimming_pool",
    ],
    PlaceTypeCategory.GOVERNMENT: [
        "city_hall",
        "courthouse",
        "embassy",
        "fire_station",
        "local_government_office",
        "police",
        "post_office",
    ],
}

# Flat list of all place types for validation
ALL_PLACE_TYPES: List[str] = [
    place_type for types in PLACE_TYPES.values() for place_type in types
]

# Common specialty to place type mappings
SPECIALTY_TO_PLACE_TYPES: Dict[str, List[str]] = {
    "dental": ["dentist", "dental_clinic"],
    "medical": ["doctor", "hospital", "medical_lab"],
    "pharmacy": ["pharmacy", "drugstore"],
    "physiotherapy": ["physiotherapist"],
    "wellness": ["spa", "wellness_center", "yoga_studio", "massage"],
    "veterinary": ["veterinary_care"],
    "beauty": ["beauty_salon", "hair_salon", "hair_care", "skin_care_clinic"],
    "fitness": ["gym", "fitness_center", "yoga_studio"],
    "restaurant": ["restaurant"],
    "cafe": ["cafe", "coffee_shop"],
    "hotel": ["hotel", "lodging", "resort_hotel"],
}

# Field mask for API requests
PLACES_FIELD_MASK = (
    "places.id,places.displayName,places.formattedAddress,"
    "places.rating,places.userRatingCount,places.priceLevel,"
    "places.nationalPhoneNumber,places.internationalPhoneNumber,"
    "places.websiteUri,places.regularOpeningHours,places.photos,"
    "places.types,places.location,places.primaryType,"
    "places.editorialSummary,places.reservable,places.delivery,places.takeout,"
    "places.paymentOptions,places.accessibilityOptions"
)

# Language name to ISO 639-1 code mapping
# Reference: https://developers.google.com/maps/faq#languagesupport
LANGUAGE_CODE_MAP: Dict[str, str] = {
    "english": "en",
    "spanish": "es",
    "french": "fr",
    "german": "de",
    "italian": "it",
    "portuguese": "pt",
    "russian": "ru",
    "japanese": "ja",
    "korean": "ko",
    "chinese": "zh",
    "arabic": "ar",
    "hindi": "hi",
    "bengali": "bn",
    "punjabi": "pa",
    "tamil": "ta",
    "telugu": "te",
    "marathi": "mr",
    "gujarati": "gu",
    "kannada": "kn",
    "malayalam": "ml",
    "thai": "th",
    "vietnamese": "vi",
    "indonesian": "id",
    "malay": "ms",
    "turkish": "tr",
    "polish": "pl",
    "dutch": "nl",
    "swedish": "sv",
    "norwegian": "no",
    "danish": "da",
    "finnish": "fi",
    "greek": "el",
    "hebrew": "he",
    "czech": "cs",
    "romanian": "ro",
    "hungarian": "hu",
    "ukrainian": "uk",
}


def _normalize_language_code(language: Optional[str]) -> str:
    """
    Normalize language input to ISO 639-1 code.

    Handles:
    - Full language names: "English" -> "en"
    - Already valid codes: "en" -> "en"
    - None/empty: returns "en"

    Args:
        language: Language name or code

    Returns:
        ISO 639-1 language code (defaults to "en")
    """
    if not language:
        return "en"

    lang_lower = language.lower().strip()

    # Already a valid 2-letter code
    if len(lang_lower) == 2:
        return lang_lower

    # Check language name mapping
    if lang_lower in LANGUAGE_CODE_MAP:
        return LANGUAGE_CODE_MAP[lang_lower]

    # Try prefix match for variations like "english (us)"
    for name, code in LANGUAGE_CODE_MAP.items():
        if lang_lower.startswith(name):
            return code

    # Default to English if unknown
    logger.warning(f"Unknown language '{language}', defaulting to 'en'")
    return "en"


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points (km)."""
    r = 6371  # Radius of earth in kilometers

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return r * c


def _get_place_types_for_specialty(specialty: Optional[str]) -> List[str]:
    """Map specialty string to Google Places API place types."""
    if not specialty:
        return []

    specialty_lower = specialty.lower().strip()

    if specialty_lower in SPECIALTY_TO_PLACE_TYPES:
        return SPECIALTY_TO_PLACE_TYPES[specialty_lower]

    if specialty_lower in ALL_PLACE_TYPES:
        return [specialty_lower]

    for category in PlaceTypeCategory:
        if specialty_lower == category.value:
            return PLACE_TYPES[category]

    return []


async def _request_location_via_rpc(
    handler: "SuperKikHandler",
    reason: str = "find nearby places",
) -> Optional[Tuple[float, float]]:
    """
    Request location from UI via RPC.

    Uses LiveKit RPC to request location from the frontend. The frontend
    should handle the 'getLocation' RPC method and return coordinates.

    Args:
        handler: SuperKikHandler instance with event bridge
        reason: Human-readable reason for requesting location

    Returns:
        Tuple of (latitude, longitude) if successful, None otherwise
    """
    if not handler._event_bridge:
        logger.warning("[LOCATION] No event bridge available for RPC")
        return None

    # Get the user's participant identity
    user_identity = _get_user_participant_identity(handler)
    if not user_identity:
        logger.warning("[LOCATION] No user participant identity for RPC")
        return None

    logger.info(f"[LOCATION] Requesting location via RPC from '{user_identity}'")

    try:
        location = await handler._event_bridge.request_location(
            destination_identity=user_identity,
            reason=reason,
            timeout=30.0,  # 30 seconds for user to respond
        )

        if location:
            lat = location.get("latitude")
            lng = location.get("longitude")
            if lat is not None and lng is not None:
                logger.info(f"[LOCATION] Received location: ({lat}, {lng})")
                # Store in preferences for future use
                _store_user_location(handler, lat, lng)
                return (float(lat), float(lng))

        logger.info("[LOCATION] User denied or no location received")
        return None

    except Exception as e:
        logger.error(f"[LOCATION] RPC request failed: {e}")
        return None


async def _request_location_from_ui(
    handler: "SuperKikHandler",
    reason: str = "find nearby places",
) -> Dict[str, Any]:
    """
    Request location from UI via data channel (fallback).

    Publishes an action block to the frontend requesting location access.
    Use this as fallback when RPC is not available.

    Args:
        handler: SuperKikHandler instance with event bridge
        reason: Human-readable reason for requesting location

    Returns:
        Action block that was sent to UI
    """
    action_id = str(uuid.uuid4())[:8]

    # Action block with ui inside data (per user request)
    action_block = {
        "event": "action_request",
        "id": action_id,
        "action": "request_location",
        "type": "location",
        "required": True,
        "data": {
            "reason": reason,
            "message": f"To {reason}, I need access to your location.",
            "permissions": ["geolocation"],
            "ui": {
                "title": "Location Required",
                "description": f"Share your location to {reason}",
                "button_text": "Share Location",
                "cancel_text": "Not Now",
            },
        },
    }

    # Publish via event bridge if available
    if handler._event_bridge:
        try:
            await handler._event_bridge.publish_data(
                data=action_block,
                topic=TOPIC_USER_ACTION,
                reliable=True,
            )
            logger.info(f"[LOCATION] Requested location from UI: {action_id}")

            # Save location request to database
            _save_location_request_to_db(handler, action_block, reason)
        except Exception as e:
            logger.error(f"Failed to publish location request: {e}")

    return action_block


def _save_location_request_to_db(
    handler: "SuperKikHandler",
    action_block: Dict[str, Any],
    reason: str,
) -> None:
    """Save location request to database for conversation history."""
    thread_id = str(handler.user_state.thread_id) if handler.user_state.thread_id else None
    if not thread_id:
        return

    try:
        msg = Message.create(
            f"Requesting location to {reason}",
            user=handler.agent,
            event=Event.AGENT_MESSAGE,
            data={
                "block_type": "location",
                "location": {
                    "action": "request",
                    "reason": reason,
                    "action_id": action_block.get("id"),
                },
            },
        )
        handler._send_callback(msg, thread_id=thread_id)
        logger.info(f"[LOCATION_DB] Saved location request: {action_block.get('id')}")
    except Exception as e:
        logger.error(f"[LOCATION_DB] Failed to save location request: {e}")


def _get_user_participant_identity(handler: "SuperKikHandler") -> Optional[str]:
    """Get the user's participant identity from the handler."""
    # Try to get from room participants
    if handler._event_bridge and handler._event_bridge._room:
        room = handler._event_bridge._room
        if hasattr(room, "remote_participants"):
            # Get first non-agent participant
            for identity, participant in room.remote_participants.items():
                if not identity.startswith("agent"):
                    return identity
    return None


def _store_user_location(
    handler: "SuperKikHandler",
    latitude: float,
    longitude: float,
) -> None:
    """Store user location in preferences and save to database."""
    preferences = getattr(handler, "_user_preferences", None)
    if preferences:
        preferences.filters["location"] = [latitude, longitude]
        logger.debug(
            f"[LOCATION] Stored location in preferences: ({latitude}, {longitude})"
        )

    # Save location response to database
    _save_location_response_to_db(handler, latitude, longitude)


def _save_location_response_to_db(
    handler: "SuperKikHandler",
    latitude: float,
    longitude: float,
) -> None:
    """Save user's location response to database for conversation history."""
    thread_id = str(handler.user_state.thread_id) if handler.user_state.thread_id else None
    if not thread_id:
        return

    try:
        # Save as user message (user shared their location)
        from super.core.context.schema import User

        user = handler.user_state.user if handler.user_state else User.add_user()
        msg = Message.create(
            "Shared location",
            user=user,
            event=Event.USER_MESSAGE,
            data={
                "block_type": "location",
                "location": {
                    "action": "shared",
                    "latitude": latitude,
                    "longitude": longitude,
                },
            },
        )
        handler._send_callback(msg, thread_id=thread_id)
        logger.info(f"[LOCATION_DB] Saved location response: ({latitude}, {longitude})")
    except Exception as e:
        logger.error(f"[LOCATION_DB] Failed to save location response: {e}")


def _build_location_required_response(
    search_type: str,
    action_block: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build a response indicating location is required.

    Args:
        search_type: Type of search (e.g., "restaurant", "gas_station")
        action_block: The action block sent to UI

    Returns:
        Response dict for the LLM
    """
    return {
        "status": "location_required",
        "action": "request_location",
        "action_id": action_block.get("id"),
        "message": (
            f"I need your location to find nearby {search_type}. "
            "I've sent a location request to your device. "
            "Please share your location and try again."
        ),
        "instructions": (
            "Tell the user you need their location to search for nearby places. "
            "A location permission prompt has been sent to their device."
        ),
    }


def _get_user_location(
    handler: "SuperKikHandler",
) -> Optional[Tuple[float, float]]:
    """
    Get user location from handler preferences or config.

    Checks in order:
    1. User preferences (from previous location share)
    2. Default location from config

    Args:
        handler: SuperKikHandler instance

    Returns:
        Tuple of (latitude, longitude) or None if not available
    """
    # Check user preferences first
    preferences = getattr(handler, "_user_preferences", None)
    if preferences and preferences.filters.get("location"):
        loc_data = preferences.filters["location"]
        if isinstance(loc_data, (list, tuple)) and len(loc_data) >= 2:
            return (float(loc_data[0]), float(loc_data[1]))

    # Check handler config for default location
    config = getattr(handler, "superkik_config", None)
    if config and config.default_location:
        return config.default_location

    return None


async def _fetch_places_text_search(
    query: str,
    location: Optional[Tuple[float, float]] = None,
    radius_m: int = 5000,
    max_results: int = 10,
    open_now: bool = False,
    language: str = "en",
    included_types: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch places using Text Search API (New).

    Use this for general text queries like "dentist near me" or "best pizza".
    Reference: https://developers.google.com/maps/documentation/places/web-service/text-search

    Args:
        query: Search text (required)
        location: Optional (lat, lng) to bias results
        radius_m: Search radius in meters (used with location)
        max_results: Maximum results (1-20)
        open_now: Filter to open places only
        language: Language code for results
        included_types: Optional place types to filter by

    Returns:
        List of place dictionaries from API response
    """
    import httpx

    api_key = GOOGLE_PLACES_API_KEY
    if not api_key:
        logger.warning("GOOGLE_API_KEY not set, returning mock data")
        return _get_mock_places(query, location)

    url = f"{GOOGLE_PLACES_BASE_URL}:searchText"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": PLACES_FIELD_MASK,
    }

    body: Dict[str, Any] = {
        "textQuery": query,
        "maxResultCount": min(max_results, 20),
        "languageCode": language,
    }

    if location:
        body["locationBias"] = {
            "circle": {
                "center": {"latitude": location[0], "longitude": location[1]},
                "radius": float(radius_m),
            }
        }

    if open_now:
        body["openNow"] = True

    if included_types:
        valid_types = [t for t in included_types if t in ALL_PLACE_TYPES]
        if valid_types:
            body["includedType"] = valid_types[0]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()
            logger.debug(f"Text search returned {len(data.get('places', []))} results")
            return data.get("places", [])

    except httpx.HTTPStatusError as e:
        logger.error(
            f"Google Places Text Search API error: {e.response.status_code} - "
            f"{e.response.text}"
        )
        return []
    except Exception as e:
        logger.error(f"Error in text search: {e}")
        return []


async def _fetch_places_nearby(
    location: Tuple[float, float],
    radius_m: int = 5000,
    max_results: int = 10,
    language: str = "en",
    included_types: Optional[List[str]] = None,
    excluded_types: Optional[List[str]] = None,
    rank_by: str = "POPULARITY",
) -> List[Dict[str, Any]]:
    """
    Fetch places using Nearby Search API (New).

    Use this when location is available and you want to find places by type.
    Reference: https://developers.google.com/maps/documentation/places/web-service/nearby-search

    Args:
        location: Required (lat, lng) center point
        radius_m: Search radius in meters (0-50000)
        max_results: Maximum results (1-20)
        language: Language code for results
        included_types: Place types to include (from Table A)
        excluded_types: Place types to exclude
        rank_by: POPULARITY (default) or DISTANCE

    Returns:
        List of place dictionaries from API response
    """
    import httpx

    api_key = GOOGLE_PLACES_API_KEY
    if not api_key:
        logger.warning("GOOGLE_API_KEY not set, returning mock data")
        return _get_mock_places("nearby", location)

    url = f"{GOOGLE_PLACES_BASE_URL}:searchNearby"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": PLACES_FIELD_MASK,
    }

    body: Dict[str, Any] = {
        "locationRestriction": {
            "circle": {
                "center": {"latitude": location[0], "longitude": location[1]},
                "radius": float(min(radius_m, 50000)),
            }
        },
        "maxResultCount": min(max_results, 20),
        "languageCode": language,
        "rankPreference": rank_by,
    }

    if included_types:
        valid_types = [t for t in included_types if t in ALL_PLACE_TYPES]
        if valid_types:
            body["includedTypes"] = valid_types

    if excluded_types:
        valid_excluded = [t for t in excluded_types if t in ALL_PLACE_TYPES]
        if valid_excluded:
            body["excludedTypes"] = valid_excluded

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()
            logger.debug(
                f"Nearby search returned {len(data.get('places', []))} results"
            )
            return data.get("places", [])

    except httpx.HTTPStatusError as e:
        logger.error(
            f"Google Places Nearby Search API error: {e.response.status_code} - "
            f"{e.response.text}"
        )
        return []
    except Exception as e:
        logger.error(f"Error in nearby search: {e}")
        return []


async def _fetch_places(
    query: Optional[str] = None,
    location: Optional[Tuple[float, float]] = None,
    radius_m: int = 5000,
    max_results: int = 10,
    open_now: bool = False,
    language: str = "en",
    included_types: Optional[List[str]] = None,
    excluded_types: Optional[List[str]] = None,
    rank_by: str = "POPULARITY",
) -> List[Dict[str, Any]]:
    """
    Smart place search that chooses the appropriate API.

    Decision logic:
    - If query is provided: Use Text Search API (with optional location bias)
    - If only location + types: Use Nearby Search API

    Args:
        query: Optional search text
        location: Optional (lat, lng) for search area
        radius_m: Search radius in meters
        max_results: Maximum results to return
        open_now: Filter to open places (Text Search only)
        language: Language code
        included_types: Place types to include
        excluded_types: Place types to exclude (Nearby Search only)
        rank_by: POPULARITY or DISTANCE (Nearby Search only)

    Returns:
        List of place dictionaries
    """
    if query:
        return await _fetch_places_text_search(
            query=query,
            location=location,
            radius_m=radius_m,
            max_results=max_results,
            open_now=open_now,
            language=language,
            included_types=included_types,
        )
    elif location and included_types:
        return await _fetch_places_nearby(
            location=location,
            radius_m=radius_m,
            max_results=max_results,
            language=language,
            included_types=included_types,
            excluded_types=excluded_types,
            rank_by=rank_by,
        )
    elif location:
        return await _fetch_places_nearby(
            location=location,
            radius_m=radius_m,
            max_results=max_results,
            language=language,
            rank_by=rank_by,
        )
    else:
        logger.warning("No query or location provided for place search")
        return []


def _get_mock_places(
    query: str, location: Optional[Tuple[float, float]] = None
) -> List[Dict[str, Any]]:
    """Return mock place data for testing without API key."""
    base_lat = location[0] if location else 28.6139
    base_lng = location[1] if location else 77.2090

    return [
        {
            "id": "mock_place_1",
            "displayName": {"text": f"Dr. Sharma's {query.title()} Clinic"},
            "formattedAddress": "123 MG Road, Near Metro Station, Delhi 110001",
            "rating": 4.5,
            "userRatingCount": 234,
            "priceLevel": "PRICE_LEVEL_MODERATE",
            "nationalPhoneNumber": "+91 98765 43210",
            "location": {"latitude": base_lat + 0.01, "longitude": base_lng + 0.01},
            "types": ["doctor", "health"],
            "regularOpeningHours": {"openNow": True},
        },
        {
            "id": "mock_place_2",
            "displayName": {"text": f"City {query.title()} Center"},
            "formattedAddress": "456 Ring Road, Sector 18, Noida 201301",
            "rating": 4.2,
            "userRatingCount": 156,
            "priceLevel": "PRICE_LEVEL_EXPENSIVE",
            "nationalPhoneNumber": "+91 98765 12345",
            "location": {"latitude": base_lat - 0.02, "longitude": base_lng + 0.02},
            "types": ["hospital", "health"],
            "regularOpeningHours": {"openNow": True},
        },
        {
            "id": "mock_place_3",
            "displayName": {"text": f"Apollo {query.title()} Hospital"},
            "formattedAddress": "789 Outer Ring Road, Gurgaon 122001",
            "rating": 4.8,
            "userRatingCount": 512,
            "priceLevel": "PRICE_LEVEL_VERY_EXPENSIVE",
            "nationalPhoneNumber": "+91 98765 67890",
            "location": {"latitude": base_lat + 0.03, "longitude": base_lng - 0.01},
            "types": ["hospital", "doctor"],
            "regularOpeningHours": {"openNow": False},
        },
    ]


def _parse_place_to_card(
    place: Dict[str, Any],
    user_location: Optional[Tuple[float, float]] = None,
) -> ProviderCard:
    """Parse Google Places API response to ProviderCard."""
    place_location = place.get("location", {})
    place_lat = place_location.get("latitude", 0)
    place_lng = place_location.get("longitude", 0)

    distance_km = 0.0
    if user_location and place_lat and place_lng:
        distance_km = _haversine_distance(
            user_location[0], user_location[1], place_lat, place_lng
        )

    price_level_map = {
        "PRICE_LEVEL_FREE": 0,
        "PRICE_LEVEL_INEXPENSIVE": 1,
        "PRICE_LEVEL_MODERATE": 2,
        "PRICE_LEVEL_EXPENSIVE": 3,
        "PRICE_LEVEL_VERY_EXPENSIVE": 4,
    }
    price_level = price_level_map.get(place.get("priceLevel", ""), None)

    opening_hours = place.get("regularOpeningHours", {})
    is_open = opening_hours.get("openNow", True)

    photo_url = None
    photos = place.get("photos", [])
    if photos:
        photo_name = photos[0].get("name", "")
        if photo_name:
            photo_url = (
                f"https://places.googleapis.com/v1/{photo_name}/media"
                f"?maxHeightPx=400&key={GOOGLE_PLACES_API_KEY}"
            )

    display_name = place.get("displayName", {})
    name = (
        display_name.get("text", "Unknown Provider")
        if isinstance(display_name, dict)
        else str(display_name)
    )

    types = place.get("types", [])
    primary_type = place.get("primaryType", "")

    specialty = _determine_specialty(primary_type, types)

    # Get phone number - use debug number if debug mode is enabled
    phone = place.get("nationalPhoneNumber") or place.get("internationalPhoneNumber")
    if PLACES_DEBUG_MODE:
        phone = PLACES_DEBUG_PHONE
        logger.debug(f"[DEBUG] Replaced phone for '{name}' with debug number")

    # Extract extra info
    extra_info = {}
    if place.get("reservable"): extra_info["reservable"] = True
    if place.get("delivery"): extra_info["delivery"] = True
    if place.get("takeout"): extra_info["takeout"] = True
    
    payment = place.get("paymentOptions", {})
    if payment.get("acceptsCreditCards"): extra_info["accepts_credit_cards"] = True
    
    accessibility = place.get("accessibilityOptions", {})
    if accessibility.get("wheelchairAccessibleEntrance"): extra_info["wheelchair_accessible"] = True

    summary = None
    edit_summary = place.get("editorialSummary")
    if edit_summary:
        summary = edit_summary.get("text")

    return ProviderCard(
        id=place.get("id", ""),
        name=name,
        rating=place.get("rating", 0.0),
        distance_km=distance_km,
        address=place.get("formattedAddress", ""),
        phone=phone,
        is_open=is_open,
        specialty=specialty,
        price_level=price_level,
        photo_url=photo_url,
        reviews_count=place.get("userRatingCount"),
        website=place.get("websiteUri"),
        place_types=types,
        extra_info=extra_info,
        summary=summary,
    )


def _determine_specialty(primary_type: str, types: List[str]) -> Optional[str]:
    """Determine specialty from primary type and types list."""
    specialty_map = {
        "doctor": "Medical",
        "dentist": "Dental",
        "dental_clinic": "Dental",
        "hospital": "Hospital",
        "pharmacy": "Pharmacy",
        "drugstore": "Pharmacy",
        "physiotherapist": "Physiotherapy",
        "chiropractor": "Chiropractic",
        "veterinary_care": "Veterinary",
        "medical_lab": "Medical Lab",
        "beauty_salon": "Beauty",
        "hair_care": "Hair Salon",
        "hair_salon": "Hair Salon",
        "barber_shop": "Barber",
        "spa": "Spa & Wellness",
        "wellness_center": "Wellness",
        "yoga_studio": "Yoga",
        "massage": "Massage",
        "gym": "Fitness",
        "fitness_center": "Fitness",
        "restaurant": "Restaurant",
        "cafe": "Cafe",
        "coffee_shop": "Coffee Shop",
        "bar": "Bar",
        "hotel": "Hotel",
        "lodging": "Lodging",
        "bank": "Banking",
        "atm": "ATM",
        "gas_station": "Gas Station",
        "car_repair": "Auto Repair",
        "car_wash": "Car Wash",
        "parking": "Parking",
        "grocery_store": "Grocery",
        "supermarket": "Supermarket",
        "shopping_mall": "Shopping",
        "movie_theater": "Cinema",
        "museum": "Museum",
        "park": "Park",
        "library": "Library",
        "school": "School",
        "university": "University",
        "airport": "Airport",
        "train_station": "Train Station",
        "bus_station": "Bus Station",
    }

    if primary_type and primary_type in specialty_map:
        return specialty_map[primary_type]

    for t in types:
        if t in specialty_map:
            return specialty_map[t]

    # Dynamic fallback: format the primary type nicely
    if primary_type:
        return primary_type.replace("_", " ").title()

    return None


async def search_providers_impl(
    handler: "SuperKikHandler",
    query: Optional[str] = None,
    specialty: Optional[str] = None,
    place_types: Optional[List[str]] = None,
    open_now: bool = False,
    max_results: int = 5,
    rank_by: str = "POPULARITY",
) -> SearchResult:
    """
    Implementation of provider search using Text Search or Nearby Search API.

    Decision logic:
    - If query is provided: Use Text Search API
    - If location + place_types (no query): Use Nearby Search API

    Args:
        handler: SuperKikHandler instance
        query: Optional search query text (triggers Text Search)
        specialty: Optional specialty filter (maps to place types)
        place_types: Optional list of Google Place types to filter
        open_now: Filter to open providers only
        max_results: Maximum results to return
        rank_by: POPULARITY or DISTANCE (Nearby Search only)

    Returns:
        SearchResult with matching providers
    """
    config = handler.superkik_config
    user_state = handler.user_state

    location: Optional[Tuple[float, float]] = None
    preferences = getattr(handler, "_user_preferences", None)
    if preferences and preferences.filters.get("location"):
        loc_data = preferences.filters["location"]
        location = (loc_data[0], loc_data[1])
    elif config.default_location:
        location = config.default_location

    included_types = place_types or []
    if specialty:
        specialty_types = _get_place_types_for_specialty(specialty)
        included_types = list(set(included_types + specialty_types))

    search_query = query
    if query and specialty and not included_types:
        search_query = f"{specialty} {query}"

    raw_language = user_state.language if user_state and user_state.language else None
    language = _normalize_language_code(raw_language)

    places = await _fetch_places(
        query=search_query,
        location=location,
        radius_m=int(config.default_search_radius_km * 1000),
        max_results=max_results,
        open_now=open_now,
        language=language,
        included_types=included_types if included_types else None,
        rank_by=rank_by,
    )

    providers = [_parse_place_to_card(p, location) for p in places]
    providers.sort(key=lambda p: (-p.rating, p.distance_km))
    providers = providers[:max_results]

    result = SearchResult(
        providers=providers,
        query=query or specialty or "nearby",
        total_count=len(providers),
        search_location=location,
        radius_km=config.default_search_radius_km,
    )

    handler._last_search_result = result

    if handler._event_bridge:
        await handler._publish_provider_cards(providers)

    return result


async def search_nearby_by_type_impl(
    handler: "SuperKikHandler",
    place_types: List[str],
    max_results: int = 5,
    rank_by: str = "DISTANCE",
) -> SearchResult:
    """
    Search nearby places by type using Nearby Search API.

    Use this when you have location and want to find specific types of places.

    Args:
        handler: SuperKikHandler instance
        place_types: List of Google Place types to search for
        max_results: Maximum results to return
        rank_by: POPULARITY or DISTANCE

    Returns:
        SearchResult with matching providers
    """
    config = handler.superkik_config
    user_state = handler.user_state

    location: Optional[Tuple[float, float]] = None
    preferences = getattr(handler, "_user_preferences", None)
    if preferences and preferences.filters.get("location"):
        loc_data = preferences.filters["location"]
        location = (loc_data[0], loc_data[1])
    elif config.default_location:
        location = config.default_location

    if not location:
        logger.warning("No location available for nearby search")
        return SearchResult(
            providers=[],
            query=", ".join(place_types),
            total_count=0,
            search_location=None,
            radius_km=config.default_search_radius_km,
        )

    raw_language = user_state.language if user_state and user_state.language else None
    language = _normalize_language_code(raw_language)

    places = await _fetch_places_nearby(
        location=location,
        radius_m=int(config.default_search_radius_km * 1000),
        max_results=max_results,
        language=language,
        included_types=place_types,
        rank_by=rank_by,
    )

    providers = [_parse_place_to_card(p, location) for p in places]

    result = SearchResult(
        providers=providers,
        query=", ".join(place_types),
        total_count=len(providers),
        search_location=location,
        radius_km=config.default_search_radius_km,
    )

    handler._last_search_result = result

    if handler._event_bridge:
        await handler._publish_provider_cards(providers)

    return result


async def get_provider_details_impl(
    handler: "SuperKikHandler",
    provider_id: str,
) -> Optional[ProviderCard]:
    """Get detailed information for a specific provider."""
    import httpx

    api_key = GOOGLE_PLACES_API_KEY
    if not api_key:
        last_result = getattr(handler, "_last_search_result", None)
        if last_result:
            for provider in last_result.providers:
                if provider.id == provider_id:
                    return provider
        return None

    url = f"{GOOGLE_PLACES_BASE_URL}/{provider_id}"

    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "id,displayName,formattedAddress,rating,userRatingCount,"
            "priceLevel,nationalPhoneNumber,internationalPhoneNumber,"
            "websiteUri,regularOpeningHours,photos,types,location"
        ),
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            place = response.json()

            location = None
            preferences = getattr(handler, "_user_preferences", None)
            if preferences and preferences.filters.get("location"):
                location = tuple(preferences.filters["location"])

            return _parse_place_to_card(place, location)

    except Exception as e:
        logger.error(f"Error fetching provider details: {e}")
        return None


class PlacesToolPlugin(ToolPlugin):
    """
    Tool plugin for provider search and discovery.

    Provides tools:
    - search_places: Unified search (auto-selects Text Search or Nearby Search)
    - get_provider_details: Get detailed info about a provider
    - request_location: Request user's location via RPC
    """

    name = "places"

    def _create_tools(self) -> List[Callable]:
        """Create places-related tool functions."""
        return [
            self._create_search_places_tool(),
            self._create_get_provider_details_tool(),
            self._create_request_location_tool(),
        ]

    def _create_search_places_tool(self) -> Callable:
        """
        Create unified search_places tool that auto-selects the right API.

        Decision logic based on parameters:
        - query provided → Text Search API
        - place_type only (no query) → Nearby Search API
        - closest/nearest intent → Nearby Search with DISTANCE ranking
        """
        try:
            from livekit.agents.llm import function_tool
        except ImportError:
            self._logger.warning("livekit.agents not available")
            return lambda: None

        handler = self._handler
        plugin = self

        @function_tool
        async def search_places(
            query: Annotated[
                Optional[str],
                Field(
                    description="Text search query like 'dentist near me', 'best pizza'."
                ),
            ] = None,
            included_types: Annotated[
                Optional[List[str]],
                Field(
                    description="List of raw Google Place types (e.g., ['hospital', 'pharmacy'])."
                ),
            ] = None,
            place_category: Annotated[
                Optional[str],
                Field(
                    description="High-level category like 'restaurant', 'doctor', 'cafe'."
                ),
            ] = None,
            open_now: Annotated[bool, Field(description="Only show open places")] = False,
            min_rating: Annotated[
                Optional[float], Field(description="Minimum rating (0.0 - 5.0)")
            ] = None,
            max_price: Annotated[
                Optional[int], Field(description="Max price level (0-4)")
            ] = None,
            radius_km: Annotated[
                Optional[float], Field(description="Search radius in kilometers")
            ] = None,
            latitude: Annotated[
                Optional[float], Field(description="Latitude for remote search area")
            ] = None,
            longitude: Annotated[
                Optional[float], Field(description="Longitude for remote search area")
            ] = None,
            find_closest: Annotated[
                bool, Field(description="Rank by distance instead of relevance")
            ] = False,
        ) -> str:
            """
            Agentic search for places using Google Places API.
            
            This tool is highly dynamic. You can search by text, category, or raw types.
            You can also filter by rating, price, and custom radius.
            """
            try:
                max_results = plugin.options.get("max_results", 5)

                if not query and not included_types and not place_category:
                    return json.dumps({"status": "error", "message": "Specify query, types, or category."})

                # Resolve location
                location = (latitude, longitude) if latitude and longitude else _get_user_location(handler)
                
                # If no location and not a global text search, request location
                if not location and not query:
                    location = await _request_location_via_rpc(handler)
                    if not location:
                        action_block = await _request_location_from_ui(handler)
                        return json.dumps(_build_location_required_response("places", action_block))

                # Resolve types
                types_to_include = included_types or []
                if place_category:
                    cat_types = _get_place_types_for_specialty(place_category)
                    types_to_include = list(set(types_to_include + cat_types))

                # Radius
                radius_m = int((radius_km or handler.superkik_config.default_search_radius_km) * 1000)
                
                # Rank
                rank_by = "DISTANCE" if find_closest else "POPULARITY"

                # Execute search
                result = await search_providers_impl(
                    handler=handler,
                    query=query,
                    place_types=types_to_include,
                    open_now=open_now,
                    max_results=max_results,
                    rank_by=rank_by,
                )

                # Post-filter by rating and price if specified (since API filtering is limited)
                providers = result.providers
                if min_rating:
                    providers = [p for p in providers if (p.rating or 0) >= min_rating]
                if max_price is not None:
                    providers = [p for p in providers if p.price_level is None or p.price_level <= max_price]
                
                if not providers:
                    return json.dumps({"status": "no_results", "message": "No matching places found."})

                providers_summary = []
                for p in providers:
                    summary = p.to_dict()
                    # Add a guide for the agent on what to ask
                    guide = []
                    if "restaurant" in p.place_types: guide.extend(["party size", "time"])
                    if "doctor" in p.place_types or "health" in p.place_types: guide.extend(["symptoms", "preferred time"])
                    if p.extra_info.get("reservable"): guide.append("reservation details")
                    summary["recommended_gathering"] = list(set(guide))
                    providers_summary.append(summary)

                return json.dumps({
                    "status": "success",
                    "count": len(providers_summary),
                    "providers": providers_summary,
                    "location_used": location,
                })

            except Exception as e:
                plugin._logger.error(f"search_places error: {e}")
                return json.dumps({"status": "error", "message": str(e)})

        return search_places

    def _create_get_provider_details_tool(self) -> Callable:
        """Create the get_provider_details function tool."""
        try:
            from livekit.agents.llm import function_tool
        except ImportError:
            self._logger.warning("livekit.agents not available")
            return lambda: None

        handler = self._handler

        @function_tool
        async def get_provider_details(
            provider_id: Annotated[
                str,
                Field(description="Provider ID from search results"),
            ],
        ) -> str:
            """
            Get detailed information about a specific provider.

            Use this when the user asks for more details about a provider from the search results.
            """
            try:
                provider = await get_provider_details_impl(handler, provider_id)

                if not provider:
                    return json.dumps(
                        {
                            "status": "not_found",
                            "message": f"Provider with ID '{provider_id}' not found.",
                        }
                    )

                return json.dumps(
                    {
                        "status": "success",
                        "provider": provider.to_dict(),
                    }
                )

            except Exception as e:
                self._logger.error(f"get_provider_details error: {e}")
                return json.dumps(
                    {
                        "status": "error",
                        "message": f"Error getting provider details: {str(e)}",
                    }
                )

        return get_provider_details

    def _create_request_location_tool(self) -> Callable:
        """
        Create a tool to request user's location via RPC.

        This tool uses LiveKit RPC to request geolocation from the frontend.
        The frontend must handle the 'getLocation' RPC method.
        """
        try:
            from livekit.agents.llm import function_tool
        except ImportError:
            self._logger.warning("livekit.agents not available")
            return lambda: None

        handler = self._handler
        plugin = self

        @function_tool
        async def request_location(
            reason: Annotated[
                str,
                Field(
                    description=(
                        "Brief reason for needing location, e.g., "
                        "'find nearby restaurants', 'get directions'"
                    )
                ),
            ] = "find nearby places",
        ) -> str:
            """
            Request the user's current location.

            Use this tool when you need the user's location for:
            - Finding nearby places (restaurants, shops, services)
            - Getting directions or distances
            - Any location-based recommendations

            The tool will prompt the user to share their location via their device.
            If successful, the location will be stored for subsequent searches.

            Returns location coordinates or an error if denied/unavailable.
            """
            try:
                # Check if we already have location
                existing_location = _get_user_location(handler)
                if existing_location:
                    plugin._logger.info(
                        f"[LOCATION] Already have location: {existing_location}"
                    )
                    return json.dumps(
                        {
                            "status": "success",
                            "message": "Location already available.",
                            "location": {
                                "latitude": existing_location[0],
                                "longitude": existing_location[1],
                            },
                        }
                    )

                # Request location via RPC
                plugin._logger.info(f"[LOCATION] Requesting location for: {reason}")
                location = await _request_location_via_rpc(
                    handler=handler,
                    reason=reason,
                )

                if location:
                    return json.dumps(
                        {
                            "status": "success",
                            "message": "Location received successfully.",
                            "location": {
                                "latitude": location[0],
                                "longitude": location[1],
                            },
                        }
                    )
                else:
                    # Fallback: send data channel notification
                    action_block = await _request_location_from_ui(
                        handler=handler,
                        reason=reason,
                    )
                    return json.dumps(
                        {
                            "status": "pending",
                            "action": "request_location",
                            "action_id": action_block.get("id"),
                            "message": (
                                "Location request sent to user's device. "
                                "Please ask the user to share their location."
                            ),
                        }
                    )

            except Exception as e:
                plugin._logger.error(f"request_location error: {e}")
                return json.dumps(
                    {
                        "status": "error",
                        "message": f"Failed to request location: {str(e)}",
                    }
                )

        return request_location

    def get_metrics(self) -> Optional[Dict[str, Any]]:
        """Return search metrics."""
        if not self._handler:
            return None

        last_result = getattr(self._handler, "_last_search_result", None)
        return {
            "last_search_count": last_result.total_count if last_result else 0,
            "last_search_query": last_result.query if last_result else None,
        }
