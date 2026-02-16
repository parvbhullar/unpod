import json
import logging

from bson import ObjectId
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from pymongo.errors import ExecutionTimeout, OperationFailure

from unpod.common.enum import (
    PrivacyType,
    SpaceType,
    KnowledgeBaseContentType,
    MediaType,
)
from unpod.common.file import getFileType
from unpod.common.helpers.calculation_helper import get_percentage
from unpod.common.constants import DATETIME_FORMAT
from unpod.common.exception import APIException206
from unpod.common.helpers.global_helper import get_product_id
from unpod.common.helpers.service_helper import send_email
from unpod.common.mongodb import MongoDBQueryManager
from unpod.common.pagination import getPagination
from unpod.common.query import get_model_unique_code
from unpod.common.string import generate_color_hex
from unpod.common.utils import get_app_info

from unpod.common.validation import validate_email
from unpod.knowledge_base.models import KnowledgeBaseConfig, DataObjectFile
from unpod.knowledge_base.utils import check_file_extension, process_store_config
from unpod.notification.services import generateNotification, createNotification
from unpod.roles.models import Roles
from unpod.roles.services import getRole
from unpod.space.email_utils import get_invite_mail_body
from unpod.space.models import (
    OrganizationAccessRequest,
    OrganizationInvite,
    OrganizationMemberRoles,
    Space,
    SpaceAccessRequest,
    SpaceInvite,
    SpaceMemberRoles,
    SpaceOrganization,
)
from unpod.common.jwt import jwt_encode_handler
from unpod.space.serializers import (
    SpaceAccessRequestUpdateSerializer,
    SpaceDetailSerializers,
    SpaceOrganizationSerializers,
)

logger = logging.getLogger(__name__)

INVITE_DICT = {
    "space": {
        "model": SpaceInvite,
        "permission_model": SpaceMemberRoles,
        "unique_code": "slug",
        "notification_type": "space",
    },
    "organization": {
        "model": OrganizationInvite,
        "permission_model": OrganizationMemberRoles,
        "unique_code": "domain_handle",
        "notification_type": "organization",
    },
}

User = get_user_model()


# fmt: off

def sendInviteMail(invite, invite_type='space'):
    product_id = get_product_id()
    app = get_app_info(product_id)
    APP_NAME = app.get("APP_NAME")
    APP_URL = app.get("APP_URL")

    name = getattr(invite, invite_type).name
    token_payload = {
        "email": invite.user_email,
        "invite_token": invite.invite_token,
        "invite_type": invite_type
    }
    token = jwt_encode_handler(token_payload)
    link = f"{APP_URL}/verify-invite?token={token}"
    html_message, subject = get_invite_mail_body(
        link,
        name,
        invite.invite_by.full_name,
        invite.valid_upto,
        invite_type,
        APP_NAME
    )
    email_from = settings.EMAIL_FROM_ADDRESS
    recipient_list = [invite.user_email, ]

    send_email(
        subject,
        email_from,
        recipient_list,
        mail_body=html_message,
        mail_type="html",
    )


def processInvitation(main_obj, user_emails, user, invite_type='space'):
    invite_model = INVITE_DICT.get(invite_type)['model']
    per_model = INVITE_DICT.get(invite_type)['permission_model']
    unique_key = INVITE_DICT.get(invite_type)['unique_code']
    notification_type = INVITE_DICT.get(invite_type)['notification_type']
    failed_email = []
    success_invite = []
    success_data = []
    already_sent = []
    duplicate_email = []

    invite_usable = User(id=None)

    today = timezone.now()
    for email in user_emails:
        if (
            validate_email(email.get('email'))
            and user.email != email.get('email')
            and email.get('email') not in duplicate_email
        ):
            query = {
                invite_type: main_obj, "user_email": email.get('email'),
                "invite_verified": False, "expired": False
            }
            check_invite = invite_model.objects.filter(**query).first()
            if check_invite:
                already_sent.append(check_invite)
                duplicate_email.append(email.get('email'))
                continue
            role, created = (Roles.objects
                             .get_or_create(role_code=email.get('role_code', 'viewer'), role_type=invite_type))
            create_data = {
                f'{invite_type}_id': main_obj.id,
                "role_id": role.id,
                "invite_by_id": user.id,
                "user_email": email.get('email'),
                "valid_from": today,
                "valid_upto": today + timezone.timedelta(days=3),
                "invite_token": get_model_unique_code(invite_model, 'invite_token', N=20)
            }
            success_invite.append(invite_model(**create_data))
            duplicate_email.append(email.get('email'))
        else:
            failed_email.append(email)
    invites = invite_model.objects.bulk_create(success_invite)
    for ind, invite in enumerate(invites):
        invite.invite_by = invite.invite_by or invite_usable
        sendInviteMail(invite, invite_type)
        success_data.append({
            "email": invite.user_email,
            'full_name': '',
            "name": getattr(invite, invite_type).name,
            "role": invite.role.role_code,
            "invite_by": invite.invite_by.full_name,
            "invite_token": invite.invite_token,
            "invite_verified": False,
            "joined": False,
            "invite_type": invite_type
        })

        unique_key_value = getattr(getattr(invite, invite_type), unique_key)
        notification_data = {
            "user_from": invite.invite_by.id,
            "user_to": invite.user_email,
            "name": getattr(invite, invite_type).name,
            "user_full_name": invite.invite_by.full_name,
            "object_id": unique_key_value,
            "event_data": {
                "name": getattr(invite, invite_type).name,
                unique_key: unique_key_value,
                "token": getattr(invite, invite_type).token,
                "role": invite.role.role_code,
                "invite_by": invite.invite_by.full_name,
                "invite_token": invite.invite_token,
            },
            "kwargs": {
                "name": getattr(invite, invite_type).name,
                "object_type": notification_type,
                "user_full_name": invite.invite_by.full_name
            }
        }
        generateNotification('invitation', invite_type, notification_data)
    for ind, invite in enumerate(already_sent):
        if not invite.invite_verified and not invite.is_joined:
            invite.valid_upto = today + timezone.timedelta(days=3)
            invite.save()
            invite.invite_by = invite.invite_by or invite_usable
            sendInviteMail(invite, invite_type)
            success_data.append({
                "email": invite.user_email,
                'full_name': '',
                "name": getattr(invite, invite_type).name,
                "role": invite.role.role_code,
                "invite_by": invite.invite_by.full_name,
                "invite_token": invite.invite_token,
                "invite_verified": False,
                "joined": False,
                "invite_type": invite_type
            })
    return success_data, failed_email


def get_space_invitation_data(user_email=None, token=None, cond=None, invite_type='space'):
    model_dict = {
        'space': SpaceInvite,
        'organization': OrganizationInvite
    }
    model = model_dict.get(invite_type)
    query = {}
    if user_email:
        query.update({"user_email": user_email})
    elif token:
        query.update({"space__token": token})
    elif cond is None:
        return []
    if cond:
        query = cond
    space_invitation = model.objects.filter(
        **query, is_joined=False, expired=False).select_related(invite_type, 'role', 'invite_by')
    space_invitation_data = []

    invite_usable = User(id=None)

    for invite in space_invitation:
        invite.invite_by = invite.invite_by or invite_usable
        space_invitation_data.append({
            "name": getattr(invite, invite_type).name,
            "role": invite.role.role_code,
            "invite_by": invite.invite_by.full_name,
            "invite_token": invite.invite_token,
            "invite_verified": invite.invite_verified,
            "valid_upto": invite.valid_upto.strftime(DATETIME_FORMAT),
            "user_email": invite.user_email,
            "joined": invite.is_joined,
            "invite_type": invite_type
        })
    return space_invitation_data


def checkJoinSpaceInvite(invite_token, user):
    invite_obj = SpaceInvite.objects.filter(invite_token=invite_token, is_joined=False, expired=False).select_related(
        'space', 'role').first()
    if not invite_obj:
        raise APIException206({"message": "Invalid Invitation"})
    if invite_obj.is_joined:
        raise APIException206({"message": "You are already member of this space"})
    if invite_obj.expired:
        raise APIException206({"message": "This Invite is Expired"})
    if user.email != invite_obj.user_email:
        raise APIException206({"message": "Invalid User/Invite Token"})
    space_mem = SpaceMemberRoles.objects.filter(user=user, space=invite_obj.space).first()
    if space_mem:
        raise APIException206({"message": "You are already member of this space"})
    space_mem = SpaceMemberRoles.objects.create(
        user=user, space=invite_obj.space, role=invite_obj.role, grant_by=invite_obj.invite_by.id
    )
    invite_obj.invite_verified = True
    invite_obj.invite_verify_dt = timezone.now()
    invite_obj.is_joined = True
    invite_obj.joined_dt = timezone.now()
    invite_obj.save()
    org_role = getRole('viewer', 'organization')
    org_user_role, created = OrganizationMemberRoles.objects.get_or_create(
        user=user,
        organization=invite_obj.space.space_organization
    )
    if created:
        org_user_role.role = org_role
        org_user_role.created_by = user.id
        org_user_role.updated_by = user.id
        org_user_role.grant_by = invite_obj.invite_by.id
        org_user_role.save()
    if invite_obj.space.privacy_type == 'private':
        Space.objects.filter(id=invite_obj.space.id).update(privacy_type='shared')
    return SpaceDetailSerializers(invite_obj.space, context={'user': user}).data


def checkJoinOrgInvite(token, user, check_verify=True):
    invite_obj = OrganizationInvite.objects.filter(invite_token=token).first()
    if not invite_obj:
        raise APIException206({"message": "Please provide valid invitation token"})
    if not invite_obj.invite_verified and check_verify:
        raise APIException206({"message": "Please verify the invitation before join"})
    if invite_obj.is_joined:
        raise APIException206({"message": "You are already member of this Organization"})
    if invite_obj.expired:
        raise APIException206({"message": "This Invite is Expired"})
    if user.email != invite_obj.user_email:
        raise APIException206({"message": "Invalid User/Invite Token"})
    organization_mem = OrganizationMemberRoles.objects.filter(user=user, organization=invite_obj.organization).first()
    if organization_mem:
        raise APIException206({"message": "You are already member of this Organization"})
    org_role = invite_obj.role
    org_user_role, created = OrganizationMemberRoles.objects.get_or_create(
        user=user,
        organization=invite_obj.organization
    )
    if created:
        org_user_role.role = org_role
        org_user_role.created_by = user.id
        org_user_role.updated_by = user.id
        org_user_role.grant_by = invite_obj.invite_by.id
        org_user_role.save()
    invite_obj.invite_verified = True
    invite_obj.invite_verify_dt = timezone.now()
    invite_obj.is_joined = True
    invite_obj.joined_dt = timezone.now()
    invite_obj.save()
    data = SpaceOrganizationSerializers(invite_obj.organization).data

    name = invite_obj.organization.name
    accept_data = {
        "event": "invitation_accepted",
        "object_type": 'organization',
        "user_from": user.id,
        "user_to": invite_obj.invite_by.id,
        "event_data": {
            "name": invite_obj.organization.name,
            "domain_handle": invite_obj.organization.domain_handle,
        },
        "title": "Invitation Accepted",
        "body": f"{user.full_name} has accepted your invitation to join the organization {name}.",
    }
    createNotification(**accept_data)

    return data


class AccessRequestService(object):
    CONST_DICT = {
        'space': {
            'model': SpaceAccessRequest,
            'relative_key': 'spacememberroles_space',
            'permission_model': SpaceMemberRoles,
            'invite_model': SpaceInvite,
            "unique_code": "slug",
            "url_segment": "spaces",
        },
        'organization': {
            'model': OrganizationAccessRequest,
            'relative_key': 'organizationmemberroles_organization',
            'permission_model': OrganizationMemberRoles,
            'invite_model': OrganizationInvite,
            "unique_code": "domain_handle",
            "url_segment": "organization",
        }
    }

    def __init__(self, request, main_obj, invite_type='space'):
        self.request = request
        self.user = request.user
        self.main_obj = main_obj
        self.invite_type = invite_type
        self.model = self.CONST_DICT.get(invite_type).get('model')
        self.relative_key = self.CONST_DICT.get(invite_type).get('relative_key')

    def checkInvite(self, check_request):
        query = {
            'user_email': check_request.user.email,
            self.invite_type: getattr(check_request, self.invite_type),
            "is_joined": False,
            'expired': False
        }
        invite_model = self.CONST_DICT.get(self.invite_type).get('invite_model')
        check_invite = invite_model.objects.filter(**query)
        if check_invite:
            invite_model.objects.filter(**query).update(is_joined=True, joined_dt=timezone.now())
        return True

    def create_access_request(self):
        query = {
            'user': self.request.user,
            self.invite_type: self.main_obj,
            "is_joined": False,
            "is_expired": False
        }
        check_request = self.model.objects.filter(**query).first()
        if check_request:
            raise APIException206({"message": f"You already requested for access for this {self.invite_type.title()}"})
        user_list = list(getattr(self.main_obj, self.relative_key).all().values_list('user__email', flat=True))
        if self.request.user.email in user_list:
            raise APIException206({"message": f"You already have access to this {self.invite_type.title()}"})
        role = getRole(role_code="viewer", role_type=self.invite_type)

        access_data = {
            "user_id": self.request.user.id,
            f"{self.invite_type}_id": self.main_obj.id,
            "role_id": role.id,
            "request_type": "access_request",
            "created_by": self.request.user.id,
            "updated_by": self.request.user.id
        }
        check_request = self.model.objects.create(**access_data)

        currentUser = self.request.user
        permission_model = self.CONST_DICT.get(self.invite_type).get('permission_model')
        unique_key = self.CONST_DICT.get(self.invite_type).get('unique_code')
        unique_key_value = getattr(self.main_obj, unique_key)
        url_segment = self.CONST_DICT.get(self.invite_type).get('url_segment')
        accept_url = f"{url_segment}/{unique_key_value}/request/{check_request.request_token}/"
        reject_url = f"{url_segment}/{unique_key_value}/request/{check_request.request_token}/reject/"

        notify_data = {
            "title": "Requested for Access",
            "object_type": self.invite_type,
            "object_id": unique_key_value,
            "user_from": currentUser.id,
            "event": "allow_cancel_action",
            "event_data": {
                "name": self.main_obj.name,
                unique_key: unique_key_value,
                "token": self.main_obj.token,
                "role": check_request.role.role_code,
                "request_type": check_request.request_type,
                "request_token": check_request.request_token,
                "allow_request": {
                    "url": accept_url,
                    "label": "Allow"
                },
                "cancel_request": {
                    "url": reject_url,
                    "label": "Reject"
                }
            }
        }

        query = {
            f"{self.invite_type}_id": self.main_obj.id,
            "role__role_code__in": ["owner", "editor"]
        }
        users = list(
            permission_model.objects.filter(**query).values_list("user__id", flat=True)
        )

        for user_id in users:
            notify_data["user_to"] = user_id
            notify_data[
                "body"
            ] = f"{currentUser.full_name} has requested for access within the {self.invite_type} {self.main_obj.name}."

            createNotification(**notify_data)

        return check_request

    def create_change_role_request(self, role_code='viewer'):
        query = {
            'user': self.request.user,
            self.invite_type: self.main_obj,
            "is_joined": False,
            "is_expired": False
        }
        check_request = self.model.objects.filter(**query).first()
        if check_request:
            raise APIException206({"message": f"You already requested for access for this {self.invite_type.title()}"})
        user_list = list(getattr(self.main_obj, self.relative_key).all().values_list('user__email', flat=True))
        if self.request.user.email not in user_list:
            raise APIException206({"message": f"You must have access to this {self.invite_type.title()} to request for role change"})
        role = getRole(role_code=role_code, role_type=self.invite_type)

        access_data = {
            "user_id": self.request.user.id,
            f"{self.invite_type}_id": self.main_obj.id,
            "role_id": role.id,
            "request_type": "change_role",
            "created_by": self.request.user.id,
            "updated_by": self.request.user.id
        }
        check_request = self.model.objects.create(**access_data)

        currentUser = self.request.user
        permission_model = self.CONST_DICT.get(self.invite_type).get('permission_model')
        unique_key = self.CONST_DICT.get(self.invite_type).get('unique_code')
        unique_key_value = getattr(self.main_obj, unique_key)
        url_segment = self.CONST_DICT.get(self.invite_type).get('url_segment')

        accept_url = f"{url_segment}/{unique_key_value}/request/{check_request.request_token}/accept-change-role/"
        reject_url = f"{url_segment}/{unique_key_value}/request/{check_request.request_token}/reject/"
        notify_data = {
            "title": "Requested for Role Change",
            "object_type": self.invite_type,
            "object_id": unique_key_value,
            "user_from": currentUser.id,
            "event": "allow_cancel_action",
            "event_data": {
                "name": self.main_obj.name,
                unique_key: unique_key_value,
                "token": self.main_obj.token,
                "role": check_request.role.role_code,
                "request_type": check_request.request_type,
                "request_token": check_request.request_token,
                "allow_request": {
                    "url": accept_url,
                    "label": "Approve"
                },
                "cancel_request": {
                    "url": reject_url,
                    "label": "Reject"
                }
            }
        }

        query = {
            f"{self.invite_type}_id": self.main_obj.id,
            "role__role_code__in": ["owner", "editor"]
        }
        users = list(
            permission_model.objects.filter(**query).values_list("user__id", flat=True)
        )

        for user_id in users:
            notify_data["user_to"] = user_id
            notify_data[
                "body"
            ] = f"{currentUser.full_name} has requested a role change for the {self.invite_type} {self.main_obj.name}."

            createNotification(**notify_data)

        return check_request

    def update_access_request(self, request_token):
        query = {
            'request_token': request_token,
            self.invite_type: self.main_obj,
        }
        check_request = self.model.objects.filter(**query).first()
        if not check_request:
            raise APIException206({"message": "Please Provide Valid Request"})
        if check_request.is_expired:
            raise APIException206({"message": "This Access Request Is Expired"})
        if check_request.is_joined:
            raise APIException206({"message": "This Access Request Already Accepted, You can't delete this request"})

        if check_request.user.id != self.request.user.id:
            raise APIException206({"message": "You are not authorized to update this request"})

        ser = SpaceAccessRequestUpdateSerializer(data=self.request.data)
        if ser.is_valid():
            role = getRole(role_code=ser.validated_data.get('role_code'), role_type=self.invite_type)
            self.model.objects.filter(id=check_request.id).update(role_id=role.id, updated_by=self.request.user.id)
            return True
        raise APIException206({"message": "There is some Validation error", "errors": ser.errors})

    def delete_access_request(self, request_token):
        query = {
            'request_token': request_token,
            self.invite_type: self.main_obj,
        }
        check_request = self.model.objects.filter(**query).first()
        if not check_request:
            raise APIException206({"message": "Please Provide Valid Request"})
        if check_request.is_expired:
            raise APIException206({"message": "This Access Request Is Expired"})
        if check_request.is_joined:
            raise APIException206({"message": "This Access Request Already Accepted, You can't delete this request"})

        if check_request.user.id != self.request.user.id:
            raise APIException206({"message": "You are not authorized to delete this request"})

        self.model.objects.filter(id=check_request.id).update(is_expired=True, updated_by=self.request.user.id)

        currentUser = self.request.user
        permission_model = self.CONST_DICT.get(self.invite_type).get('permission_model')
        unique_key = self.CONST_DICT.get(self.invite_type).get('unique_code')
        unique_key_value = getattr(self.main_obj, unique_key)

        notify_data = {
            "title": "Access Request Deleted",
            "object_type": self.invite_type,
            "object_id": unique_key_value,
            "user_from": currentUser.id,
            "event": "access_request_deleted",
            "body": None,
            "event_data": {
                "name": self.main_obj.name,
                unique_key: unique_key_value,
                "request_type": check_request.request_type,
                "request_token": check_request.request_token,
            }
        }

        query = {
            f"{self.invite_type}_id": self.main_obj.id,
            "role__role_code__in": ["owner", "editor"]
        }
        users = list(
            permission_model.objects.filter(**query).values_list("user__id", flat=True)
        )

        for user_id in users:
            notify_data["user_to"] = user_id
            notify_data[
                "body"
            ] = f"{currentUser.full_name} has deleted access request for the {self.invite_type} {self.main_obj.name}."

            createNotification(**notify_data)

        return True

    def reject_access_request(self, request_token):
        query = {
            'request_token': request_token,
            self.invite_type: self.main_obj,
        }
        check_request = self.model.objects.filter(**query).first()
        if not check_request:
            raise APIException206({"message": "Please Provide Valid Request"})
        if check_request.is_expired:
            raise APIException206({"message": "This Access Request Is Expired"})
        if check_request.is_joined:
            raise APIException206({"message": "This Access Request Already Accepted, You can't reject this request"})

        self.model.objects.filter(id=check_request.id).update(is_expired=True, updated_by=self.request.user.id)

        currentUser = self.request.user
        unique_key = self.CONST_DICT.get(self.invite_type).get('unique_code')
        unique_key_value = getattr(self.main_obj, unique_key)

        notify_data = {
            "title": "Request Rejected",
            "object_type": self.invite_type,
            "object_id": unique_key_value,
            "user_from": currentUser.id,
            "user_to": check_request.user.id,
            "event": "access_request_accepted",
            "body": f"Your request for the {self.invite_type} {self.main_obj.name} has been rejected.",
            "event_data": {
                "name": self.main_obj.name,
                unique_key: unique_key_value,
                "role": check_request.role.role_code,
            }
        }

        createNotification(**notify_data)
        return True

    def resend_access_request(self, request_token):
        query = {
            'request_token': request_token,
            self.invite_type: self.main_obj,
        }
        check_request = self.model.objects.filter(**query).first()
        if not check_request:
            raise APIException206({"message": "Please Provide Valid Request"})
        if check_request.is_expired:
            raise APIException206({"message": "This Access Request Is Expired"})
        if check_request.is_joined:
            raise APIException206({"message": "This Access Request Already Accepted, You can't resend this request"})
        user_list = list(getattr(self.main_obj, self.relative_key).all().values_list('user__email', flat=True))
        if self.request.user.email in user_list:
            raise APIException206({"message": f"You already have access to this {self.invite_type.title()}"})
        self.model.objects.filter(id=check_request.id).update(is_expired=True, updated_by=self.request.user.id)
        access_data = {
            "user_id": check_request.user.id,
            f"{self.invite_type}_id": getattr(check_request, self.invite_type).id,
            "role_id": check_request.role.id,
            "request_type": check_request.request_type,
            "created_by": self.request.user.id,
            "updated_by": self.request.user.id
        }
        check_request = self.model.objects.create(**access_data)

        currentUser = self.request.user
        permission_model = self.CONST_DICT.get(self.invite_type).get('permission_model')
        unique_key = self.CONST_DICT.get(self.invite_type).get('unique_code')
        unique_key_value = getattr(self.main_obj, unique_key)
        url_segment = self.CONST_DICT.get(self.invite_type).get('url_segment')
        accept_url = f"{url_segment}/{unique_key_value}/request/{check_request.request_token}/"
        reject_url = f"{url_segment}/{unique_key_value}/request/{check_request.request_token}/reject/"

        notify_data = {
            "title": "Requested for Access",
            "object_type": self.invite_type,
            "object_id": unique_key_value,
            "user_from": currentUser.id,
            "event": "allow_cancel_action",
            "event_data": {
                "name": self.main_obj.name,
                unique_key: unique_key_value,
                "token": self.main_obj.token,
                "role": check_request.role.role_code,
                "request_type": check_request.request_type,
                "request_token": check_request.request_token,
                "allow_request": {
                    "url": accept_url,
                    "label": "Allow"
                },
                "cancel_request": {
                    "url": reject_url,
                    "label": "Reject"
                }
            }
        }

        query = {
            f"{self.invite_type}_id": self.main_obj.id,
            "role__role_code__in": ["owner", "editor"]
        }
        users = list(
            permission_model.objects.filter(**query).values_list("user__id", flat=True)
        )

        for user_id in users:
            notify_data["user_to"] = user_id
            notify_data[
                "body"
            ] = f"{currentUser.full_name} has requested for access within the {self.invite_type} {self.main_obj.name}."

            createNotification(**notify_data)

        return check_request

    def accept_access_request(self, request_token):
        query = {
            'request_token': request_token,
            self.invite_type: self.main_obj,
        }
        check_request = self.model.objects.filter(**query).first()
        if not check_request:
            raise APIException206({"message": "Please Provide Valid Request"})
        if check_request.is_expired:
            raise APIException206({"message": "This Access Request Is Expired"})
        user_list = list(getattr(self.main_obj, self.relative_key).all().values_list('user__email', flat=True))
        if check_request.user.email in user_list:
            raise APIException206({"message": f"You already have access to this {self.invite_type.title()}"})

        per_model = self.CONST_DICT.get(self.invite_type).get('permission_model')
        create_data = {
            "user": check_request.user,
            self.invite_type: getattr(check_request, self.invite_type),
            "role": check_request.role,
            "grant_by": self.request.user.id
        }
        mem_obj = per_model.objects.create(**create_data)
        today = timezone.now()
        update_data = {
            "request_verified": True,
            "is_joined": True,
            "request_verify_dt": today,
            "joined_dt": today,
            "updated_by": self.request.user.id
        }
        self.model.objects.filter(id=check_request.id).update(**update_data)
        success_data = {
            'email': mem_obj.user.email,
            'full_name': mem_obj.user.full_name,
            'role': mem_obj.role.role_code,
            'join_date': mem_obj.created.strftime(DATETIME_FORMAT),
            'joined': True
        }
        self.checkInvite(check_request)
        if self.invite_type == 'space':
            org_role = getRole('viewer', 'organization')
            org_user_role, created = OrganizationMemberRoles.objects.get_or_create(
                user=check_request.user,
                organization=check_request.space.space_organization
            )
            if created:
                org_user_role.role = org_role
                org_user_role.created_by = self.request.user.id
                org_user_role.updated_by = self.request.user.id
                org_user_role.grant_by = self.request.user.id
                org_user_role.save()

        currentUser = self.request.user
        unique_key = self.CONST_DICT.get(self.invite_type).get('unique_code')
        unique_key_value = getattr(self.main_obj, unique_key)

        notify_data = {
            "title": "Access Request Accepted",
            "object_type": self.invite_type,
            "object_id": unique_key_value,
            "user_from": currentUser.id,
            "user_to": mem_obj.user.id,
            "event": "access_request_accepted",
            "body": f"Your access request for the {self.invite_type} {self.main_obj.name} has been accepted.",
            "event_data": {
                "name": self.main_obj.name,
                unique_key: unique_key_value,
                "role": check_request.role.role_code,
            }
        }

        createNotification(**notify_data)
        return success_data

    def accept_change_role_request(self, request_token):
        query = {
            'request_token': request_token,
            self.invite_type: self.main_obj,
        }
        check_request = self.model.objects.filter(**query).first()

        if not check_request:
            raise APIException206({"message": "Please Provide Valid Request"})
        if check_request.is_expired:
            raise APIException206({"message": "This Access Request Is Expired"})
        user_list = list(getattr(self.main_obj, self.relative_key).all().values_list('user__email', flat=True))

        if self.request.user.email not in user_list:
            raise APIException206({"message": f"You must have access to this {self.invite_type.title()} to request for role change"})

        per_model = self.CONST_DICT.get(self.invite_type).get('permission_model')
        create_data = {
            "user": check_request.user,
            self.invite_type: getattr(check_request, self.invite_type),
        }
        mem_obj = per_model.objects.get(**create_data)
        if mem_obj:
            mem_obj.is_active = True
            mem_obj.role = check_request.role
            mem_obj.grant_by = self.request.user.id
            mem_obj.save()

        today = timezone.now()
        update_data = {
            "request_verified": True,
            "is_joined": True,
            "request_verify_dt": today,
            "joined_dt": today,
            "updated_by": self.request.user.id
        }
        self.model.objects.filter(id=check_request.id).update(**update_data)
        success_data = {
            'email': mem_obj.user.email,
            'full_name': mem_obj.user.full_name,
            'role': mem_obj.role.role_code,
            'join_date': mem_obj.created.strftime(DATETIME_FORMAT),
            'joined': True
        }

        currentUser = self.request.user
        unique_key = self.CONST_DICT.get(self.invite_type).get('unique_code')
        unique_key_value = getattr(self.main_obj, unique_key)

        notify_data = {
            "title": "Role Change Request Accepted",
            "object_type": self.invite_type,
            "object_id": unique_key_value,
            "user_from": currentUser.id,
            "user_to": mem_obj.user.id,
            "event": "access_request_accepted",
            "body": f"Your role change request for the {self.invite_type} {self.main_obj.name} has been accepted.",
            "event_data": {
                "name": self.main_obj.name,
                unique_key: unique_key_value,
                "role": check_request.role.role_code,
            }
        }

        createNotification(**notify_data)

        return success_data


def get_anonymous_space():
    anonymous_domain = 'unpod@anonymous.tv'
    check_org = SpaceOrganization.objects.filter(domain_handle=anonymous_domain, is_private_domain=True).first()
    if not check_org:
        check_org = SpaceOrganization.objects.create(
            name='Anonymous Organization',
            domain_handle=anonymous_domain,
            domain=anonymous_domain,
            is_private_domain=True,
            color=generate_color_hex()
        )
    check_space = Space.objects.filter(space_organization=check_org, name='general').first()
    if not check_space:
        check_space = Space.objects.create(
            name='general',
            description='general',
            space_organization=check_org,
            is_default=True
        )
    return check_space


def add_org(space_list):
    org_ids = set()
    for space in space_list:
        org_id = space.get('space_organization_id', None)
        if org_id:
            org_ids.add(org_id)
    if not org_ids:
        return space_list
    org_obj = SpaceOrganization.objects.filter(id__in=list(org_ids))
    org_dict = {}
    for org in org_obj:
        org_dict[org.id] = SpaceOrganizationSerializers(org).data
    for space in space_list:
        space['organization'] = org_dict.get(space.pop('space_organization_id', 0))
    return space_list


def createSpace(input_data, user, organization):
    space_obj = Space.objects.create(
        name=input_data.get("name", ""),
        description=input_data.get("description", ""),
        space_organization_id=organization.id,
        privacy_type=input_data.get("privacy_type", PrivacyType.public.name),
        created_by=user.id,
        updated_by=user.id,
        space_type=input_data.get("space_type"),
        content_type=input_data.get("content_type"),
    )

    store_data = {"space": space_obj}
    if (
        input_data.get("space_type") == SpaceType.knowledge_base.name
        or space_obj.content_type != KnowledgeBaseContentType.general.name
    ):
        schema_data = input_data.pop("schema", {})
        KnowledgeBaseConfig.objects.create(
            knowledge_base=space_obj, schema=schema_data
        )
        store_data["schema"] = schema_data

    if "files" in input_data:
        files = input_data.pop("files")
        data_objs = []
        for file in files:
            if not check_file_extension(file.name, space_obj.content_type):
                continue
            object_type = getFileType(file.name)
            content = {}
            if object_type == MediaType.json.name:
                content = json.load(file)
            data_objs.append(
                DataObjectFile(
                    file=file,
                    name=file.name,
                    knowledge_base=space_obj,
                    object_type=object_type,
                    content=content,
                )
            )
        if data_objs:
            DataObjectFile.objects.bulk_create(data_objs)
        store_data["files"] = data_objs
    owner_role, created = Roles.objects.get_or_create(
        role_code="owner", role_name="Owner", role_type="space"
    )
    space_user_role, created = SpaceMemberRoles.objects.get_or_create(
        user=user,
        space=space_obj,
        role=owner_role,
        created_by=user.id,
        updated_by=user.id,
    )
    space_user_role.grant_by = user.id
    space_user_role.save()

    invite_list = input_data.get("invite_list", None)
    if invite_list:
        processInvitation(space_obj, invite_list, user)

    try:
        if (
            input_data.get("space_type") == SpaceType.knowledge_base.name
            or space_obj.content_type != KnowledgeBaseContentType.general.name
        ):
            process_store_config(store_data)
    except Exception as ex:
        print("Exception - process_store_config", ex)

    return space_obj


def get_organization_by_domain_handle(domain_handle):
    """Helper to get organization by domain handle"""
    try:
        return SpaceOrganization.objects.filter(domain_handle=domain_handle).first()
    except Exception as e:
        logger.error(
            f"Error getting organization by domain: {str(e)}", exc_info=True
        )
        return None


def fetch_space_analytics(space_ids):
    """
    Fetch analytics data for given spaces from MongoDB.
    Args:
        space_ids: List of space IDs to fetch analytics for.
    Returns:
        dict: Analytics data retrieved from MongoDB.
    """
    collection_name = "runs"
    # Convert space_ids to strings for MongoDB query
    space_id_strs = [str(sid) for sid in space_ids] if space_ids else []
    query = {
        "space_id": {"$in": space_id_strs},
        "$or": [
            {"call_analytics": {"$ne": {}, "$exists": True}},
            {"execution_analytics": {"$ne": {}, "$exists": True}}
        ]
    }

    try:
        collection = MongoDBQueryManager.get_collection(collection_name)

        # Add maxTimeMS to limit query execution time to 10 seconds
        cursor = collection.aggregate([
            {
                "$match": query
            }, {
                "$facet": {
                    "call_analytics": [
                        {
                            "$group": {
                                "_id": None,
                                "total_calls": {"$sum": "$call_analytics.total_calls"},
                                "interested": {"$sum": "$call_analytics.interested"},
                                "call_back": {"$sum": "$call_analytics.call_back"},
                                "send_details": {"$sum": "$call_analytics.send_details"},
                                "not_interested": {"$sum": "$call_analytics.not_interested"},
                                "not_connected": {"$sum": "$call_analytics.not_connected"},
                                "failed": {"$sum": "$call_analytics.failed"},
                                "avg_success_score": {"$sum": "$call_analytics.quality_metrics.avg_success_score"},
                            }
                        },
                    ],
                    "execution_analytics": [
                        {
                            "$group": {
                                "_id": None,
                                "total_tasks": {"$sum": "$execution_analytics.total_tasks"},
                                "completed": {"$sum": "$execution_analytics.completed"},
                                "failed": {"$sum": "$execution_analytics.failed"},
                                "pending": {"$sum": "$execution_analytics.pending"},
                                "in_progress": {"$sum": "$execution_analytics.in_progress"},
                            }
                        },

                    ],
                }
            }
        ], maxTimeMS=10000)  # 10 second timeout for the aggregation
        result = list(cursor)

        if len(result) > 0:
            data = list(result)[0]
            call_analytics = data.get("call_analytics")[0] if data.get("call_analytics") else {}
            call_analytics.pop("_id", 0)

            execution_analytics = data.get("execution_analytics")[0] if data.get("execution_analytics") else {}
            total_tasks = execution_analytics.get("total_tasks", 0)
            completed = execution_analytics.get("completed", 0)
            execution_analytics.pop("_id", 0)

            analytics = {
                "call_analytics": {
                    **call_analytics,
                },
                "call_status": {
                    **execution_analytics,
                    "success_rate": get_percentage(completed, total_tasks)
                }
            }

            return analytics
        return None
    except (ExecutionTimeout, OperationFailure) as e:
        logger.error(f"MongoDB analytics query timeout for space {space_ids}: {e}")
        return None
    except Exception as e:
        logger.error(f"MongoDB analytics query failed for space {space_ids}: {e}")
        return None


def get_calls(space_id: int, query_params: dict):
    collection_name = "tasks"
    skip, limit = getPagination(query_params, 30)
    query = {
        "space_id": str(space_id),
        "output": {"$ne": {}, "$exists": True},
    }
    exclude_fields = [
        "retry_attempt",
        "thread_id",
        "user_info",
        "call_analytics",
        "execution_analytics",
        "last_status_change",
        "provider",
        "attachments",
        "ref_id",
        "failure_count",
        "last_failure_reason",
        "scheduled_timestamp",
        "task",
        "collection_ref",
        "run_id",
        "user_org_id",
        "user",
        "space_id",
        "modified",
        "assignee",
        "execution_type",
        "input.token",
        "input.quality",
        "output.call_id",
        "output.contact_number",
        "output.transcript",
        "output.post_call_data",
        "output.metadata",
        "output.call_end_reason",
        "output.recording_url",
        "output.start_time",
        "output.end_time",
        "output.assistant_number",
        "output.call_summary",
        "output.duration",
        "output.cost",
        "output.call_status",
    ]
    projection = {field: 0 for field in exclude_fields}

    try:
        collection = MongoDBQueryManager.get_collection(collection_name)
        cursor = (
            collection.find(query, projection, sort=[("_id", -1)]).skip(skip).limit(limit)
        )
        total_count = collection.count_documents(query)
        records = list(cursor)

        data = []

        for record in records:
            output = {}
            status = record.get("status")
            output_data = record.get("output", {})
            input_data = record.get("input", {})
            call_type = output_data.get("call_type", "")
            if not call_type:
                call_type = input_data.get("call_type", "")

            customer = output_data.get("customer", None)
            contact_number = input_data.get("contact_number", "")
            output["name"] = input_data.get("name", "")

            if status == "completed":
                if call_type == "inbound" and customer:
                    output["number"] = customer

                elif call_type == "outbound" and contact_number:
                    output["number"] = contact_number
                else:
                    output["number"] = customer
            else:
                output["number"] = contact_number

            record_id = str(record.pop("_id"))
            output["task_id"] = record.get("task_id")
            output["status"] = status
            output["call_type"] = call_type
            output["created"] = record.get("created")


            if "created" not in record:
                output["created"] = ObjectId(record_id).generation_time.strftime(
                    "%Y-%m-%dT%H:%M:%S"
                )

            data.append(output)

        return total_count, data
    except (ExecutionTimeout, OperationFailure) as e:
        logger.error(f"MongoDB analytics query timeout for space {space_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"MongoDB analytics query failed for space {space_id}: {e}")
        return None


def get_task_details(task_id: str):
    collection_name = "tasks"
    try:
        collection = MongoDBQueryManager.get_collection(collection_name)
        record = collection.find_one({"task_id": task_id})
        record_id = str(record.pop("_id"))
        record["id"] = record_id
        return record
    except (ExecutionTimeout, OperationFailure) as e:
        logger.error(f"MongoDB analytics query timeout for space {task_id}: {e}")
        return None

