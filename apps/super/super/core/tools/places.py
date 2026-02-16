"""
Places Tool - Provider discovery using Google Places API.

Provides search functionality for local businesses and services.
This tool is stateless and can be used with any orchestrator.
"""

import os
from math import atan2, cos, radians, sin, sqrt
from typing import Any, Dict, List, Optional, Tuple

from super.core.logging import logging as app_logging
from super.core.tools.base import BaseTool, ToolCategory, ToolResult

logger = app_logging.get_logger("tools.places")

GOOGLE_PLACES_API_KEY = os.getenv("GEMINI_API_KEY", "")
GOOGLE_PLACES_BASE_URL = "https://places.googleapis.com/v1/places"

PLACES_FIELD_MASK = (
    "places.id,places.displayName,places.formattedAddress,"
    "places.rating,places.userRatingCount,places.priceLevel,"
    "places.nationalPhoneNumber,places.internationalPhoneNumber,"
    "places.websiteUri,places.regularOpeningHours,places.photos,"
    "places.types,places.location,places.primaryType"
)


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points (km)."""
    r = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return r * c


def _parse_place(
    place: Dict[str, Any],
    user_location: Optional[Tuple[float, float]] = None,
) -> Dict[str, Any]:
    """Parse Google Places API response to a dict."""
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

    display_name = place.get("displayName", {})
    name = (
        display_name.get("text", "Unknown")
        if isinstance(display_name, dict)
        else str(display_name)
    )

    opening_hours = place.get("regularOpeningHours", {})

    return {
        "id": place.get("id", ""),
        "name": name,
        "rating": place.get("rating", 0.0),
        "distance_km": round(distance_km, 2),
        "address": place.get("formattedAddress", ""),
        "phone": place.get("nationalPhoneNumber")
        or place.get("internationalPhoneNumber"),
        "is_open": opening_hours.get("openNow", True),
        "price_level": price_level_map.get(place.get("priceLevel", ""), None),
        "reviews_count": place.get("userRatingCount"),
        "website": place.get("websiteUri"),
        "types": place.get("types", []),
        "primary_type": place.get("primaryType", ""),
        "location": {"lat": place_lat, "lng": place_lng} if place_lat else None,
    }


async def _fetch_places_text_search(
    query: str,
    location: Optional[Tuple[float, float]] = None,
    radius_m: int = 5000,
    max_results: int = 10,
    open_now: bool = False,
    language: str = "en",
) -> List[Dict[str, Any]]:
    """Fetch places using Text Search API."""
    import httpx

    api_key = GOOGLE_PLACES_API_KEY
    if not api_key:
        logger.warning("GOOGLE_API_KEY not set")
        return []

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

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()
            return data.get("places", [])
    except Exception as e:
        logger.error(f"Places text search error: {e}")
        return []


class PlacesTool(BaseTool):
    """
    Tool for searching places using Google Places API.

    Supports text-based queries with optional location bias.
    """

    name = "search_places"
    description = "Search for local businesses and services using Google Places API"
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
                        "description": "Search query (e.g., 'dentist near me', 'best pizza')",
                    },
                    "latitude": {
                        "type": "number",
                        "description": "Latitude for location bias",
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude for location bias",
                    },
                    "radius_km": {
                        "type": "number",
                        "description": "Search radius in kilometers (default: 5)",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum results to return (default: 5)",
                    },
                    "open_now": {
                        "type": "boolean",
                        "description": "Only return currently open places",
                    },
                },
                "required": ["query"],
            },
        }

    async def execute(
        self,
        query: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius_km: float = 5.0,
        max_results: int = 5,
        open_now: bool = False,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute places search."""
        location = (latitude, longitude) if latitude and longitude else None

        places = await _fetch_places_text_search(
            query=query,
            location=location,
            radius_m=int(radius_km * 1000),
            max_results=max_results,
            open_now=open_now,
        )

        if not places:
            return ToolResult(
                success=True,
                data={"places": [], "count": 0, "query": query},
                metadata={"message": "No places found"},
            )

        parsed = [_parse_place(p, location) for p in places]
        parsed.sort(key=lambda p: (-p.get("rating", 0), p.get("distance_km", 999)))

        return ToolResult(
            success=True,
            data={"places": parsed[:max_results], "count": len(parsed), "query": query},
        )
