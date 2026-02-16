from django.urls import path
from unpod.notification.views import NotificationViewSet


urlpatterns = [
    path(
        "",
        NotificationViewSet.as_view({"get": "list", "put": "update"}),
        name="notification-list",
    ),
    path(
        "stream/",
        NotificationViewSet.as_view({"get": "stream"}),
        name="notification-stream",
    ),
    path(
        "send-notification/",
        NotificationViewSet.as_view({"get": "send_notification"}),
        name="send-notification",
    ),
    # Centrifugo endpoints
    path(
        "centrifugo/config/",
        NotificationViewSet.as_view({"get": "centrifugo_config"}),
        name="centrifugo-config",
    ),
    path(
        "centrifugo/token/",
        NotificationViewSet.as_view({"get": "centrifugo_token"}),
        name="centrifugo-token",
    ),
    path(
        "centrifugo/subscription-token/",
        NotificationViewSet.as_view({"post": "centrifugo_subscription_token"}),
        name="centrifugo-subscription-token",
    ),
    # Action endpoints (keep at end to avoid path conflicts)
    path(
        "<str:token>/",
        NotificationViewSet.as_view({"post": "action"}),
        name="notification-action",
    ),
    path(
        "<str:token>/expire/",
        NotificationViewSet.as_view({"get": "expire_notification"}),
        name="expire_notification",
    ),
]
