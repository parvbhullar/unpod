from django.utils import timezone
from unpod.common.exception import APIException206
from unpod.notification.models import Notification
from unpod.notification.services import createNotification
from unpod.space.models import SpaceInvite, OrganizationInvite
from unpod.space.services import checkJoinOrgInvite, checkJoinSpaceInvite


def processInvitationEvent(action, notification, user):
    if action == "decline":
        event_data = notification.event_data
        object_type = notification.object_type
        if object_type == "space":
            (
                SpaceInvite.objects.filter(
                    invite_token=event_data["invite_token"]
                ).update(expired=True, expired_dt=timezone.now())
            )
        elif object_type == "organization":
            (
                OrganizationInvite.objects.filter(
                    invite_token=event_data["invite_token"]
                ).update(expired=True, expired_dt=timezone.now())
            )

        name = event_data.get("name", "")
        decline_data = {
            "event": "invitation_declined",
            "object_type": object_type,
            "user_from": user.id,
            "user_to": notification.user_from,
            "event_data": event_data,
            "title": "Invitation Declined",
            "body": f"{user.full_name} has declined your invitation to join the {object_type} {name}.",
        }
        createNotification(**decline_data)

        return {}
    elif action == "accept":
        event_data = notification.event_data
        object_type = notification.object_type
        data = None
        if object_type == "space":
            data = checkJoinSpaceInvite(event_data["invite_token"], user)
        elif object_type == "organization":
            data = checkJoinOrgInvite(
                event_data["invite_token"], user, check_verify=False
            )

        name = event_data.get("name", "")
        accept_data = {
            "event": "invitation_accepted",
            "object_type": object_type,
            "user_from": user.id,
            "user_to": notification.user_from,
            "event_data": event_data,
            "title": "Invitation Accepted",
            "body": f"{user.full_name} has accepted your invitation to join the {object_type} {name}.",
        }
        createNotification(**accept_data)

        return data
    raise APIException206({"message": "Invalid Action"})


def expireNotification(object_type, invite_token):
    Notification.objects.filter(
        event_data__invite_token=invite_token, object_type=object_type
    ).update(expired=True, read=True)
    return {}
