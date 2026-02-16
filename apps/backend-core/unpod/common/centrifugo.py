"""
Centrifugo integration for real-time notifications.

This module provides Centrifugo client functionality for publishing events
and generating connection/subscription tokens for clients.

Uses the official `cent` library for Centrifugo HTTP API communication.

Usage:
    from unpod.common.centrifugo import (
        publish_to_user,
        publish_to_users,
        generate_connection_token,
        generate_subscription_token,
    )

    # Publish notification to a user
    publish_to_user(user_id, notification_data, event_type="notification")

    # Generate token for frontend connection
    token = generate_connection_token(user_id)
"""
import time
import logging
import threading
from typing import Dict, Any, List, Optional
from functools import lru_cache

import jwt
from django.conf import settings

logger = logging.getLogger(__name__)

# Thread-safe singleton lock
_client_lock = threading.Lock()
_client_instance = None


class CentrifugoConfig:
    """Centrifugo configuration container with validation."""

    def __init__(self):
        self.enabled: bool = getattr(settings, "CENTRIFUGO_ENABLED", False)
        self.url: str = getattr(settings, "CENTRIFUGO_URL", "").rstrip("/")
        self.api_key: str = getattr(settings, "CENTRIFUGO_API_KEY", "")
        self.token_hmac_secret_key: str = getattr(
            settings, "CENTRIFUGO_TOKEN_HMAC_SECRET_KEY", ""
        )
        self.user_channel_prefix: str = getattr(
            settings, "CENTRIFUGO_USER_CHANNEL_PREFIX", "user"
        )
        self.session_channel_prefix: str = getattr(
            settings, "CENTRIFUGO_SESSION_CHANNEL_PREFIX", "session"
        )
        self.token_expire_minutes: int = getattr(
            settings, "CENTRIFUGO_TOKEN_EXPIRE_MINUTES", 60
        )

    def is_valid(self) -> bool:
        """Check if configuration is valid for operation."""
        return bool(self.enabled and self.url and self.api_key)

    def validate_for_tokens(self) -> None:
        """Validate configuration for token generation."""
        if not self.token_hmac_secret_key:
            raise ValueError(
                "CENTRIFUGO_TOKEN_HMAC_SECRET_KEY must be configured for token generation"
            )


@lru_cache(maxsize=1)
def get_config() -> CentrifugoConfig:
    """Get cached Centrifugo configuration."""
    return CentrifugoConfig()


def is_centrifugo_enabled() -> bool:
    """Check if Centrifugo is configured and enabled."""
    return get_config().is_valid()


def _get_client():
    """
    Get thread-safe singleton Centrifugo client instance.

    Returns:
        cent.Client instance or None if not configured
    """
    global _client_instance

    if _client_instance is not None:
        return _client_instance

    config = get_config()
    if not config.is_valid():
        return None

    with _client_lock:
        # Double-check after acquiring lock
        if _client_instance is not None:
            return _client_instance

        try:
            from cent import Client

            _client_instance = Client(
                config.url,
                api_key=config.api_key,
                timeout=5.0,
            )
            logger.info(f"Centrifugo client initialized for {config.url}")
        except ImportError:
            logger.error(
                "cent library not installed. Install with: pip install cent"
            )
            return None
        except Exception as e:
            logger.error(f"Failed to initialize Centrifugo client: {e}")
            return None

    return _client_instance


def generate_channel_name(post_slug: str, space_token: str) -> str:
    """
    Generate unique channel name for Centrifugo session.

    Format: session:{post_slug}-{space_token}-{timestamp}

    Args:
        post_slug: The post identifier slug
        space_token: The space token identifier

    Returns:
        Unique channel name string
    """
    config = get_config()
    timestamp = int(time.time() * 1000)
    return f"{config.session_channel_prefix}:{post_slug}-{space_token}-{timestamp}"


def get_user_channel(user_id: str) -> str:
    """
    Get the channel name for a user's personal notifications.

    Args:
        user_id: The user ID

    Returns:
        Channel name in format "{prefix}:{user_id}"
    """
    config = get_config()
    return f"{config.user_channel_prefix}:{user_id}"


def generate_connection_token(
    user_id: str,
    expire_minutes: Optional[int] = None,
    info: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a JWT connection token for Centrifugo client authentication.

    The token allows a client to establish a connection to Centrifugo server.

    Args:
        user_id: The user ID (becomes 'sub' claim in JWT)
        expire_minutes: Token expiration in minutes (uses config default if None)
        info: Optional user info to attach to connection

    Returns:
        JWT token string

    Raises:
        ValueError: If CENTRIFUGO_TOKEN_HMAC_SECRET_KEY is not configured
    """
    config = get_config()
    config.validate_for_tokens()

    expire_minutes = expire_minutes or config.token_expire_minutes

    claims = {
        "sub": str(user_id),
        "exp": int(time.time()) + (expire_minutes * 60),
    }

    if info:
        claims["info"] = info

    return jwt.encode(claims, config.token_hmac_secret_key, algorithm="HS256")


def generate_subscription_token(
    user_id: str,
    channel: str,
    expire_minutes: Optional[int] = None,
    info: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a JWT subscription token for a private/protected channel.

    Required when channel has protected or private namespace configuration.

    Args:
        user_id: The user ID
        channel: The full channel name to authorize subscription
        expire_minutes: Token expiration in minutes (uses config default if None)
        info: Optional subscription info

    Returns:
        JWT token string

    Raises:
        ValueError: If CENTRIFUGO_TOKEN_HMAC_SECRET_KEY is not configured
    """
    config = get_config()
    config.validate_for_tokens()

    expire_minutes = expire_minutes or config.token_expire_minutes

    claims = {
        "sub": str(user_id),
        "channel": channel,
        "exp": int(time.time()) + (expire_minutes * 60),
    }

    if info:
        claims["info"] = info

    return jwt.encode(claims, config.token_hmac_secret_key, algorithm="HS256")


def _build_payload(data: Dict[str, Any], event_type: str) -> Dict[str, Any]:
    """Build standardized event payload."""
    return {
        "event": event_type,
        "data": data,
        "timestamp": time.time(),
    }


def publish_to_user(
    user_id: str,
    data: Dict[str, Any],
    event_type: str = "notification",
) -> bool:
    """
    Publish an event to a user's personal channel.

    Args:
        user_id: The user ID
        data: The event data payload
        event_type: The event type identifier (default: "notification")

    Returns:
        True if published successfully, False otherwise
    """
    if not is_centrifugo_enabled():
        logger.debug("Centrifugo disabled, skipping publish to user %s", user_id)
        return False

    client = _get_client()
    if client is None:
        return False

    channel = get_user_channel(user_id)
    payload = _build_payload(data, event_type)

    try:
        from cent import PublishRequest

        request = PublishRequest(channel=channel, data=payload)
        client.publish(request)
        logger.debug("Published %s event to user %s", event_type, user_id)
        return True
    except Exception as e:
        logger.error("Failed to publish to user %s: %s", user_id, e)
        return False


def publish_to_users(
    user_ids: List[str],
    data: Dict[str, Any],
    event_type: str = "notification",
) -> bool:
    """
    Publish an event to multiple users' channels using broadcast.

    Args:
        user_ids: List of user IDs
        data: The event data payload
        event_type: The event type identifier (default: "notification")

    Returns:
        True if broadcast successfully, False otherwise
    """
    if not user_ids:
        return True

    if not is_centrifugo_enabled():
        logger.debug("Centrifugo disabled, skipping broadcast to %d users", len(user_ids))
        return False

    client = _get_client()
    if client is None:
        return False

    channels = [get_user_channel(uid) for uid in user_ids]
    payload = _build_payload(data, event_type)

    try:
        from cent import BroadcastRequest

        request = BroadcastRequest(channels=channels, data=payload)
        client.broadcast(request)
        logger.debug("Broadcast %s event to %d users", event_type, len(user_ids))
        return True
    except Exception as e:
        logger.error("Failed to broadcast to %d users: %s", len(user_ids), e)
        return False


def publish_to_channel(
    channel: str,
    data: Dict[str, Any],
    event_type: str = "notification",
) -> bool:
    """
    Publish an event to a specific named channel.

    Use this for organization-wide or space-wide broadcasts.

    Args:
        channel: The full channel name (e.g., "org:token", "space:id")
        data: The event data payload
        event_type: The event type identifier (default: "notification")

    Returns:
        True if published successfully, False otherwise
    """
    if not is_centrifugo_enabled():
        logger.debug("Centrifugo disabled, skipping publish to channel %s", channel)
        return False

    client = _get_client()
    if client is None:
        return False

    payload = _build_payload(data, event_type)

    try:
        from cent import PublishRequest

        request = PublishRequest(channel=channel, data=payload)
        client.publish(request)
        logger.debug("Published %s event to channel %s", event_type, channel)
        return True
    except Exception as e:
        logger.error("Failed to publish to channel %s: %s", channel, e)
        return False


def reset_client() -> None:
    """
    Reset the client instance. Useful for testing or configuration changes.
    """
    global _client_instance
    with _client_lock:
        _client_instance = None
    get_config.cache_clear()
