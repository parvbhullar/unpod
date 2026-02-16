"""
Utility functions for LiveKit Test SDK

Provides:
- Token generation
- Room management helpers
- Configuration loading
"""

import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

try:
    from livekit import api as lk_api

    LIVEKIT_AVAILABLE = True
except ImportError:
    LIVEKIT_AVAILABLE = False


@dataclass
class LiveKitConfig:
    """LiveKit connection configuration"""

    url: str
    api_key: str
    api_secret: str

    @classmethod
    def from_env(cls) -> "LiveKitConfig":
        """Load configuration from environment variables"""
        return cls(
            url=os.getenv("LIVEKIT_URL", "ws://localhost:7880"),
            api_key=os.getenv("LIVEKIT_API_KEY", "devkey"),
            api_secret=os.getenv("LIVEKIT_API_SECRET", "secret"),
        )


@dataclass
class TokenGrants:
    """Token permission grants"""

    room_join: bool = True
    room: Optional[str] = None
    can_publish: bool = True
    can_subscribe: bool = True
    can_publish_data: bool = True
    is_agent: bool = False


def generate_room_name(prefix: str = "test-room") -> str:
    """
    Generate a unique room name

    Args:
        prefix: Prefix for the room name

    Returns:
        Unique room name string
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    return f"{prefix}-{timestamp}-{unique_id}"


def generate_identity(prefix: str = "user") -> str:
    """
    Generate a unique participant identity

    Args:
        prefix: Prefix for the identity

    Returns:
        Unique identity string
    """
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def generate_token(
    config: LiveKitConfig,
    room_name: str,
    identity: str,
    name: Optional[str] = None,
    grants: Optional[TokenGrants] = None,
    ttl_seconds: int = 3600,
) -> str:
    """
    Generate a LiveKit access token

    Args:
        config: LiveKit configuration
        room_name: Room to grant access to
        identity: Participant identity
        name: Display name (defaults to identity)
        grants: Token permission grants
        ttl_seconds: Token time-to-live in seconds

    Returns:
        JWT token string

    Raises:
        RuntimeError: If livekit-python is not installed
    """
    if not LIVEKIT_AVAILABLE:
        raise RuntimeError(
            "livekit-python not installed. Install with: pip install livekit"
        )

    if grants is None:
        grants = TokenGrants(room=room_name)

    token = lk_api.AccessToken(config.api_key, config.api_secret)
    token.with_identity(identity)
    token.with_name(name or identity)
    token.with_ttl(ttl_seconds)

    video_grants = lk_api.VideoGrants(
        room_join=grants.room_join,
        room=grants.room or room_name,
        can_publish=grants.can_publish,
        can_subscribe=grants.can_subscribe,
        can_publish_data=grants.can_publish_data,
    )

    if grants.is_agent:
        video_grants.agent = True

    token.with_grants(video_grants)

    return token.to_jwt()


def generate_user_token(
    config: LiveKitConfig, room_name: str, user_name: str = "TestUser"
) -> tuple[str, str]:
    """
    Generate token for a user participant

    Args:
        config: LiveKit configuration
        room_name: Room to join
        user_name: Display name for the user

    Returns:
        Tuple of (token, identity)
    """
    identity = generate_identity("user")
    token = generate_token(
        config=config,
        room_name=room_name,
        identity=identity,
        name=user_name,
        grants=TokenGrants(room=room_name, is_agent=False),
    )
    return token, identity


def generate_agent_token(
    config: LiveKitConfig, room_name: str, agent_name: str = "voice-agent"
) -> tuple[str, str]:
    """
    Generate token for an agent participant

    Args:
        config: LiveKit configuration
        room_name: Room to join
        agent_name: Display name for the agent

    Returns:
        Tuple of (token, identity)
    """
    identity = generate_identity("agent")
    token = generate_token(
        config=config,
        room_name=room_name,
        identity=identity,
        name=agent_name,
        grants=TokenGrants(room=room_name, is_agent=True),
    )
    return token, identity


async def create_room(
    config: LiveKitConfig,
    room_name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    empty_timeout: int = 300,
    max_participants: int = 10,
) -> str:
    """
    Create a LiveKit room via API

    Args:
        config: LiveKit configuration
        room_name: Optional room name (auto-generated if not provided)
        metadata: Optional room metadata
        empty_timeout: Seconds before empty room is deleted
        max_participants: Maximum participants allowed

    Returns:
        Room name

    Raises:
        RuntimeError: If livekit-python is not installed
    """
    if not LIVEKIT_AVAILABLE:
        raise RuntimeError("livekit-python not installed")

    if room_name is None:
        room_name = generate_room_name()

    api_url = config.url.replace("ws://", "http://").replace("wss://", "https://")
    lk = lk_api.LiveKitAPI(api_url, config.api_key, config.api_secret)

    import json

    room_metadata = json.dumps(metadata) if metadata else None

    request = lk_api.CreateRoomRequest(
        name=room_name,
        metadata=room_metadata,
        empty_timeout=empty_timeout,
        max_participants=max_participants,
    )

    await lk.room.create_room(request)
    return room_name


async def delete_room(config: LiveKitConfig, room_name: str) -> bool:
    """
    Delete a LiveKit room

    Args:
        config: LiveKit configuration
        room_name: Room to delete

    Returns:
        True if successful
    """
    if not LIVEKIT_AVAILABLE:
        return False

    try:
        api_url = config.url.replace("ws://", "http://").replace("wss://", "https://")
        lk = lk_api.LiveKitAPI(api_url, config.api_key, config.api_secret)
        await lk.room.delete_room(lk_api.DeleteRoomRequest(room=room_name))
        return True
    except Exception:
        return False


async def list_rooms(config: LiveKitConfig) -> list:
    """
    List all active rooms

    Args:
        config: LiveKit configuration

    Returns:
        List of room information dictionaries
    """
    if not LIVEKIT_AVAILABLE:
        return []

    try:
        api_url = config.url.replace("ws://", "http://").replace("wss://", "https://")
        lk = lk_api.LiveKitAPI(api_url, config.api_key, config.api_secret)
        response = await lk.room.list_rooms(lk_api.ListRoomsRequest())

        return [
            {
                "name": room.name,
                "num_participants": room.num_participants,
                "created_at": room.creation_time,
                "metadata": room.metadata,
            }
            for room in response.rooms
        ]
    except Exception:
        return []


async def get_room_participants(config: LiveKitConfig, room_name: str) -> list:
    """
    Get participants in a room

    Args:
        config: LiveKit configuration
        room_name: Room to query

    Returns:
        List of participant information dictionaries
    """
    if not LIVEKIT_AVAILABLE:
        return []

    try:
        api_url = config.url.replace("ws://", "http://").replace("wss://", "https://")
        lk = lk_api.LiveKitAPI(api_url, config.api_key, config.api_secret)
        response = await lk.room.list_participants(
            lk_api.ListParticipantsRequest(room=room_name)
        )

        return [
            {
                "identity": p.identity,
                "name": p.name,
                "state": str(p.state),
                "joined_at": p.joined_at,
            }
            for p in response.participants
        ]
    except Exception:
        return []


async def send_data_to_room(
    config: LiveKitConfig,
    room_name: str,
    data: bytes,
    destination_identities: Optional[list] = None,
    topic: Optional[str] = None,
) -> bool:
    """
    Send data message to room participants

    Args:
        config: LiveKit configuration
        room_name: Target room
        data: Data to send
        destination_identities: Specific participants to send to (None = all)
        topic: Optional topic for the message

    Returns:
        True if successful
    """
    if not LIVEKIT_AVAILABLE:
        return False

    try:
        api_url = config.url.replace("ws://", "http://").replace("wss://", "https://")
        lk = lk_api.LiveKitAPI(api_url, config.api_key, config.api_secret)

        request = lk_api.SendDataRequest(
            room=room_name,
            data=data,
            kind=lk_api.DataPacketKind.RELIABLE,
            destination_identities=destination_identities or [],
            topic=topic,
        )

        await lk.room.send_data(request)
        return True
    except Exception:
        return False


def validate_config(config: LiveKitConfig) -> tuple[bool, str]:
    """
    Validate LiveKit configuration

    Args:
        config: Configuration to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not config.url:
        return False, "LIVEKIT_URL is not set"

    if not config.api_key:
        return False, "LIVEKIT_API_KEY is not set"

    if not config.api_secret:
        return False, "LIVEKIT_API_SECRET is not set"

    if not config.url.startswith(("ws://", "wss://")):
        return False, "LIVEKIT_URL must start with ws:// or wss://"

    return True, ""


def get_ws_url_from_http(http_url: str) -> str:
    """Convert HTTP URL to WebSocket URL"""
    return http_url.replace("http://", "ws://").replace("https://", "wss://")


def get_http_url_from_ws(ws_url: str) -> str:
    """Convert WebSocket URL to HTTP URL"""
    return ws_url.replace("ws://", "http://").replace("wss://", "https://")
