from django.conf import settings
from rest_framework import viewsets
from rest_framework.response import Response
from unpod.common.pagination import getPaginator
from unpod.common.renderers import UnpodJSONRenderer
from unpod.common.serializer import CommonSerializer
from unpod.notification.models import Notification
from unpod.notification.utlis import processInvitationEvent


class NotificationViewSet(viewsets.GenericViewSet):
    serializer_class = CommonSerializer
    renderer_classes = [
        UnpodJSONRenderer,
    ]

    def list(self, request, *args, **kwargs):
        column_list = [
            "title",
            "body",
            "object_type",
            "event",
            "event_data",
            "token",
            "expired",
            "read",
            "created",
        ]
        objs = (
            Notification.objects.filter(
                user_to__in=[request.user.email, str(request.user.id)]
            )
            .values(*column_list)
            .order_by("read", "-id")
        )
        total_count = objs.count()
        unread_count = objs.filter(read=False).count()
        paginator, page, page_size = getPaginator(objs, request)
        page_data = paginator.page(page)
        return Response(
            {
                "data": page_data.object_list,
                "count": total_count,
                "unread_count": unread_count,
            },
            status=200,
        )

    def update(self, request, *args, **kwargs):
        token = request.data.get("token")
        read_all = request.data.get("read_all", False)
        if token or read_all:
            objs = Notification.objects.filter(
                user_to__in=[request.user.email, str(request.user.id)]
            )
            if token:
                objs = objs.filter(token=token, read=False)
            elif read_all:
                objs = objs.filter(read=False)
            objs.update(read=True)
        return Response({"message": "Notification Read Updated"}, status=200)

    def expire_notification(self, request, token):
        notification = Notification.objects.filter(
            token=token, user_to__in=[request.user.email, str(request.user.id)]
        ).first()

        if not notification:
            return Response({"message": "Invalid Notification"}, status=206)

        notification.expired = True
        notification.read = True
        notification.save()

        return Response({"message": "Notifications Expired"}, status=200)

    def action(self, request, *args, **kwargs):
        token = kwargs.get("token")
        notification = Notification.objects.filter(
            user_to__in=[request.user.email, str(request.user.id)],
            token=token,
        ).first()

        if not notification:
            return Response({"message": "Invalid Notification"}, status=206)

        if notification.expired:
            return Response(
                {"message": "Notification is expired", "data": {"expired": True}},
                status=206,
            )
        if notification.read:
            notification.expired = True
            notification.save()

            return Response(
                {"message": "Notification is expired", "data": {"expired": True}},
                status=200,
            )

        action = request.data.get("action")
        event = notification.event
        if event == "invitation":
            data = processInvitationEvent(action, notification, request.user)
            notification.expired = True
            notification.read = True
            notification.save()
            return Response({"data": data, "message": "Action Processed"}, status=200)

        return Response({"data": {}, "message": "Invalid Event"}, status=206)

    def stream(self, request, *args, **kwargs):
        """
        SSE endpoint for real-time notifications.

        This endpoint establishes a Server-Sent Events connection that streams
        notifications to the authenticated user in real-time.

        Usage:
            GET /api/v1/notifications/stream/
            Headers: Authorization: JWT <token>

        Response:
            Content-Type: text/event-stream
            Events: connected, notification, heartbeat (comments)
        """
        from unpod.notification.sse import create_sse_response

        user_id = str(request.user.id)
        return create_sse_response(user_id)

    def send_notification(self, request, *args, **kwargs):
        # This is a placeholder for sending notification logic
        # In a real implementation, you would extract necessary data from the request
        # and call the createNotification service function.
        from unpod.notification.sse import broadcast_notification

        user_id = str(request.user.id)
        notification_data = {
            "token": "sample_token",
            "title": "Sample Notification",
            "body": "This is a sample notification body.",
            "event": "sample_event",
            "object_type": "sample_object",
            "event_data": {},
            "read": False,
            "expired": False,
            "created": None,
        }

        broadcast_notification(user_id, notification_data, event_type="notification")

        return Response({"message": "Notification sent (placeholder)"}, status=200)

    def centrifugo_config(self, request, *args, **kwargs):
        """
        Get Centrifugo configuration for frontend.

        Returns connection URL and status. Frontend uses this to determine
        whether to connect to Centrifugo or fall back to Django SSE.

        GET /api/v1/notifications/centrifugo/config/

        Response:
            {
                "enabled": true,
                "url": "wss://centrifugo.example.com/connection/websocket",
                "user_channel": "user:123"
            }
        """
        from unpod.common.centrifugo import is_centrifugo_enabled, get_user_channel

        user_id = str(request.user.id)
        enabled = is_centrifugo_enabled()

        response_data = {
            "enabled": enabled,
            "url": getattr(settings, "CENTRIFUGO_WS_URL", "") if enabled else "",
            "user_channel": get_user_channel(user_id) if enabled else "",
        }

        return Response(response_data, status=200)

    def centrifugo_token(self, request, *args, **kwargs):
        """
        Get Centrifugo connection token for the authenticated user.

        This token allows the frontend to establish a connection to Centrifugo server.

        GET /api/v1/notifications/centrifugo/token/

        Response:
            {
                "token": "eyJ...",
                "expires_in": 3600
            }
        """
        from unpod.common.centrifugo import (
            is_centrifugo_enabled,
            generate_connection_token,
            get_config,
        )

        if not is_centrifugo_enabled():
            return Response(
                {"error": "Centrifugo is not enabled"},
                status=400
            )

        user_id = str(request.user.id)
        config = get_config()

        try:
            token = generate_connection_token(
                user_id,
                info={"email": request.user.email}
            )
            return Response({
                "token": token,
                "expires_in": config.token_expire_minutes * 60,
            }, status=200)
        except ValueError as e:
            return Response({"error": str(e)}, status=500)

    def centrifugo_subscription_token(self, request, *args, **kwargs):
        """
        Get subscription token for a private/protected channel.

        POST /api/v1/notifications/centrifugo/subscription-token/
        Body: {"channel": "user:123"}

        Response:
            {
                "token": "eyJ...",
                "channel": "user:123",
                "expires_in": 3600
            }
        """
        from unpod.common.centrifugo import (
            is_centrifugo_enabled,
            generate_subscription_token,
            get_user_channel,
            get_config,
        )

        if not is_centrifugo_enabled():
            return Response(
                {"error": "Centrifugo is not enabled"},
                status=400
            )

        channel = request.data.get("channel")
        if not channel:
            return Response(
                {"error": "channel is required"},
                status=400
            )

        user_id = str(request.user.id)
        user_channel = get_user_channel(user_id)

        # Validate user can access this channel
        # Users can only subscribe to their own personal channel
        if channel != user_channel:
            return Response(
                {"error": "Unauthorized channel access"},
                status=403
            )

        config = get_config()

        try:
            token = generate_subscription_token(user_id, channel)
            return Response({
                "token": token,
                "channel": channel,
                "expires_in": config.token_expire_minutes * 60,
            }, status=200)
        except ValueError as e:
            return Response({"error": str(e)}, status=500)
