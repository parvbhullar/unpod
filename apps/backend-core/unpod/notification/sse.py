"""
Server-Sent Events (SSE) implementation for real-time notifications.

This module provides SSE functionality for pushing notifications to connected clients.
Supports two backends:
1. Centrifugo (when CENTRIFUGO_ENABLED=True) - Recommended for production
2. Redis pub/sub (fallback) - Used when Centrifugo is disabled

When Centrifugo is enabled:
- Notifications are published to Centrifugo server via HTTP API
- Frontend connects directly to Centrifugo for SSE/WebSocket
- The Django /stream/ endpoint still works as fallback

When Centrifugo is disabled:
- Uses Redis pub/sub for message distribution
- Django streams SSE directly to clients via /stream/ endpoint
"""
import json
import logging
import time
from typing import Generator, Optional, Dict, Any

import redis
from django.conf import settings
from django.http import StreamingHttpResponse

logger = logging.getLogger(__name__)

# SSE Configuration defaults
SSE_HEARTBEAT_INTERVAL = getattr(settings, "SSE_HEARTBEAT_INTERVAL", 30)  # seconds
SSE_RETRY_TIMEOUT = getattr(settings, "SSE_RETRY_TIMEOUT", 3000)  # milliseconds
SSE_CHANNEL_PREFIX = getattr(settings, "SSE_CHANNEL_PREFIX", "unpod:sse:notifications:")


def get_redis_connection() -> redis.Redis:
    """Get Redis connection from Django cache settings."""
    redis_url = settings.CACHES.get("default", {}).get(
        "LOCATION", "redis://127.0.0.1:6379"
    )
    return redis.from_url(redis_url)


def format_sse_message(
    data: Dict[str, Any],
    event: Optional[str] = None,
    event_id: Optional[str] = None,
    retry: Optional[int] = None,
) -> str:
    """
    Format data as an SSE message.

    Args:
        data: The data to send (will be JSON encoded)
        event: Optional event type name
        event_id: Optional event ID for client reconnection
        retry: Optional retry timeout in milliseconds

    Returns:
        Formatted SSE message string
    """
    lines = []

    if event_id:
        lines.append(f"id: {event_id}")

    if event:
        lines.append(f"event: {event}")

    if retry:
        lines.append(f"retry: {retry}")

    # JSON encode the data
    json_data = json.dumps(data)
    lines.append(f"data: {json_data}")

    # SSE messages end with double newline
    return "\n".join(lines) + "\n\n"


def format_sse_comment(comment: str = "heartbeat") -> str:
    """Format a comment line for SSE (used for keepalive)."""
    return f": {comment}\n\n"


class SSEBroadcaster:
    """
    Handles broadcasting notifications to SSE clients.

    Automatically selects the appropriate backend:
    - Centrifugo when enabled
    - Redis pub/sub as fallback

    Usage:
        broadcaster = SSEBroadcaster()
        broadcaster.publish(user_id, notification_data)
    """

    def __init__(self):
        self._redis = None
        self._use_centrifugo = None

    @property
    def use_centrifugo(self) -> bool:
        """Check if Centrifugo backend should be used."""
        if self._use_centrifugo is None:
            from unpod.common.centrifugo import is_centrifugo_enabled
            self._use_centrifugo = is_centrifugo_enabled()
        return self._use_centrifugo

    @property
    def redis(self) -> redis.Redis:
        """Lazy Redis connection (only used when Centrifugo is disabled)."""
        if self._redis is None:
            self._redis = get_redis_connection()
        return self._redis

    def get_channel_name(self, user_id: str) -> str:
        """Get the Redis channel name for a user."""
        return f"{SSE_CHANNEL_PREFIX}{user_id}"

    def publish(
        self,
        user_id: str,
        notification_data: Dict[str, Any],
        event_type: str = "notification",
    ) -> int:
        """
        Publish a notification to a user's SSE channel.

        Automatically routes to Centrifugo or Redis based on configuration.

        Args:
            user_id: The user ID to send the notification to
            notification_data: The notification data dict
            event_type: The SSE event type (default: "notification")

        Returns:
            Number of subscribers that received the message (Redis only),
            or 1 if successfully published to Centrifugo, 0 on failure
        """
        if self.use_centrifugo:
            return self._publish_centrifugo(user_id, notification_data, event_type)
        return self._publish_redis(user_id, notification_data, event_type)

    def _publish_centrifugo(
        self,
        user_id: str,
        notification_data: Dict[str, Any],
        event_type: str,
    ) -> int:
        """Publish via Centrifugo."""
        from unpod.common.centrifugo import publish_to_user

        success = publish_to_user(user_id, notification_data, event_type)
        return 1 if success else 0

    def _publish_redis(
        self,
        user_id: str,
        notification_data: Dict[str, Any],
        event_type: str,
    ) -> int:
        """Publish via Redis pub/sub."""
        channel = self.get_channel_name(user_id)
        message = {
            "event": event_type,
            "data": notification_data,
            "timestamp": time.time(),
        }
        return self.redis.publish(channel, json.dumps(message))

    def publish_to_multiple(
        self,
        user_ids: list,
        notification_data: Dict[str, Any],
        event_type: str = "notification",
    ):
        """
        Publish a notification to multiple users.

        Args:
            user_ids: List of user IDs to send the notification to
            notification_data: The notification data dict
            event_type: The SSE event type
        """
        if self.use_centrifugo:
            from unpod.common.centrifugo import publish_to_users
            publish_to_users(user_ids, notification_data, event_type)
        else:
            for user_id in user_ids:
                self._publish_redis(user_id, notification_data, event_type)


class SSEStreamGenerator:
    """
    Generates SSE stream for a specific user.

    Subscribes to Redis pub/sub and yields SSE-formatted messages.
    Includes heartbeat mechanism to keep connections alive.

    Note: This class is used when clients connect to Django's /stream/ endpoint.
    When Centrifugo is enabled, clients should connect directly to Centrifugo instead.
    """

    def __init__(self, user_id: str, heartbeat_interval: int = SSE_HEARTBEAT_INTERVAL):
        self.user_id = user_id
        self.heartbeat_interval = heartbeat_interval
        self._redis = None
        self._pubsub = None
        self._running = False
        self._last_heartbeat = time.time()

    @property
    def redis(self) -> redis.Redis:
        """Lazy Redis connection."""
        if self._redis is None:
            self._redis = get_redis_connection()
        return self._redis

    def get_channel_name(self) -> str:
        """Get the Redis channel name for this user."""
        return f"{SSE_CHANNEL_PREFIX}{self.user_id}"

    def _send_heartbeat_if_needed(self) -> Optional[str]:
        """Send heartbeat if interval has passed."""
        now = time.time()
        if now - self._last_heartbeat >= self.heartbeat_interval:
            self._last_heartbeat = now
            return format_sse_comment("heartbeat")
        return None

    def stream(self) -> Generator[str, None, None]:
        """
        Generate SSE stream for the user.

        Yields:
            SSE-formatted message strings
        """
        self._running = True

        try:
            # Send initial retry timeout
            yield format_sse_message(
                {"status": "connected", "user_id": self.user_id},
                event="connected",
                retry=SSE_RETRY_TIMEOUT,
            )

            # Subscribe to user's channel
            self._pubsub = self.redis.pubsub()
            channel = self.get_channel_name()
            self._pubsub.subscribe(channel)

            self._last_heartbeat = time.time()

            while self._running:
                # Check for messages with timeout
                message = self._pubsub.get_message(timeout=1.0)

                if message and message["type"] == "message":
                    try:
                        payload = json.loads(message["data"])
                        yield format_sse_message(
                            payload.get("data", {}),
                            event=payload.get("event", "notification"),
                            event_id=str(payload.get("timestamp", time.time())),
                        )
                    except (json.JSONDecodeError, KeyError):
                        # Invalid message format, skip
                        pass

                # Send heartbeat if needed
                heartbeat = self._send_heartbeat_if_needed()
                if heartbeat:
                    yield heartbeat

        except GeneratorExit:
            # Client disconnected
            pass
        finally:
            self.stop()

    def stop(self):
        """Stop the stream and cleanup resources."""
        self._running = False
        if self._pubsub:
            try:
                self._pubsub.unsubscribe()
                self._pubsub.close()
            except Exception:
                pass
            self._pubsub = None


def create_sse_response(user_id: str) -> StreamingHttpResponse:
    """
    Create a StreamingHttpResponse for SSE.

    Note: When Centrifugo is enabled, clients should connect directly to
    Centrifugo server instead of using this endpoint.

    Args:
        user_id: The user ID to stream notifications for

    Returns:
        StreamingHttpResponse with SSE content type and headers
    """
    generator = SSEStreamGenerator(user_id)

    response = StreamingHttpResponse(
        generator.stream(), content_type="text/event-stream"
    )

    # SSE-specific headers
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"  # Disable nginx buffering

    # CORS headers for SSE
    response["Access-Control-Allow-Origin"] = "*"
    response[
        "Access-Control-Allow-Headers"
    ] = "Authorization, Content-Type, Org-Handle, AppType, Product-Id"
    response["Access-Control-Allow-Credentials"] = "true"

    return response


# Global broadcaster instance
_broadcaster = None


def get_broadcaster() -> SSEBroadcaster:
    """Get the global SSE broadcaster instance."""
    global _broadcaster
    if _broadcaster is None:
        _broadcaster = SSEBroadcaster()
    return _broadcaster


def broadcast_notification(
    user_id: str, notification_data: Dict[str, Any], event_type: str = "notification"
) -> int:
    """
    Convenience function to broadcast a notification.

    Automatically routes to Centrifugo or Redis based on configuration.

    Args:
        user_id: The user ID to send the notification to
        notification_data: The notification data dict
        event_type: The SSE event type

    Returns:
        Number of subscribers that received the message
    """
    return get_broadcaster().publish(user_id, notification_data, event_type)


def broadcast_to_users(
    user_ids: list, data: Dict[str, Any], event_type: str = "notification"
):
    """
    Broadcast an event to multiple users.

    Automatically routes to Centrifugo or Redis based on configuration.

    Args:
        user_ids: List of user IDs to send the event to
        data: The event data dict
        event_type: The SSE event type
    """
    return get_broadcaster().publish_to_multiple(user_ids, data, event_type)


# Event type constants for consistency
class SSEEventTypes:
    """Standard SSE event types used in the application."""

    NOTIFICATION = "notification"
    INVITATION = "invitation"
    POST_CREATED = "post_created"
    POST_UPDATED = "post_updated"
    COMMENT_ADDED = "comment_added"
    REACTION_ADDED = "reaction_added"
    MEMBER_JOINED = "member_joined"
    MEMBER_LEFT = "member_left"
    ACTIVITY_UPDATE = "activity_update"
    METRICS_UPDATE = "metrics_update"
    SUBSCRIPTION_UPDATE = "subscription_update"
    WALLET_UPDATE = "wallet_update"
