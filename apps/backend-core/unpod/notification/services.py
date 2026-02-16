from unpod.notification.constants import NOTIFICATION_MESSAGE_EVENT
from unpod.notification.models import Notification

from unpod.notification.sse import broadcast_notification
from unpod.users.models import User


def createNotification(**kwargs):
    obj = Notification.objects.create(**kwargs)

    # Broadcast notification via SSE if user_to is set
    if str(obj.user_to).isdigit():
        user_id = str(obj.user_to)
    else:
        request_user = User.objects.filter(email=obj.user_to).first()
        user_id = str(request_user.id) if request_user else None

    if user_id:
        notification_data = {
            "token": obj.token,
            "title": obj.title,
            "body": obj.body,
            "event": obj.event,
            "object_type": obj.object_type,
            "event_data": obj.event_data or {},
            "read": obj.read,
            "expired": obj.expired,
            "created": obj.created.isoformat() if obj.created else None,
        }
        broadcast_notification(user_id, notification_data, event_type="notification")

    return obj


def processInviteNotification(data, object_type):
    create_data = {
        "event": "invitation",
        "object_type": object_type,
        "object_id": data.pop("object_id"),
        "user_from": data.pop("user_from"),
        "user_to": data.pop("user_to"),
        "event_data": data.get("event_data", {}),
        "title": "New Invitation Received",
        "body": NOTIFICATION_MESSAGE_EVENT["invitation"].format(
            **data.get("kwargs", {})
        ),
    }
    createNotification(**create_data)


def processRequestNotification(data, object_type):
    pass


def generateNotification(event, object_type, data):
    EVENT_MAP = {
        "invitation": processInviteNotification,
        # "access_request": ''
    }
    try:
        return EVENT_MAP[event](data, object_type)
    except Exception as e:
        print("Exception in generateNotification", str(e))
