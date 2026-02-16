from django.contrib.auth import authenticate, user_logged_in
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework.authtoken.models import Token

# Import JWT handlers from our Django 4.2 compatible implementation
from unpod.common.jwt import (
    jwt_encode_handler,
    jwt_payload_handler,
)
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from unpod.common.exception import APIException206
from unpod.common.serializer import RestrictedFileField
from unpod.common.storage_backends import imagekitBackend
from unpod.common.validation import fetch_email_domain, validate_email_type
from unpod.space.constants import SPACE_LIST_ALL
from unpod.space.models import OrganizationInvite, SpaceInvite
from unpod.space.serializers import SpaceListSerializers, SpaceOrganizationSerializers
from unpod.users.utils import check_user, checkUserOragaization

from .models import UserBasicDetail, UserInviteToken, User, UserDevice
from datetime import datetime, timedelta


class JWTSerializer(serializers.Serializer):
    """
    JWT authentication serializer for Django 4.2+.
    Replaces old JSONWebTokenSerializer from djangorestframework-jwt.
    """
    username_field = 'email'  # Use email as username field

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically add username field
        self.fields[self.username_field] = serializers.CharField()
        self.fields['password'] = serializers.CharField(write_only=True)

    def validate(self, attrs):
        # Django's ModelBackend expects 'username' parameter, not 'email'
        # So we pass the email value as 'username'
        email = attrs.get(self.username_field)
        password = attrs.get("password")

        credentials = {
            "username": email,  # Pass email as username for authentication
            "password": password,
        }
        if all(credentials.values()):
            user = authenticate(**credentials)
            if user:
                if user and not user.verify_email:
                    msg = {
                        "message": "User account email verification not completed",
                        "email_verified": "false",
                    }
                    raise APIException206(
                        detail=msg,
                    )
                if user and not user.is_active:
                    msg = {
                        "message": "User account is not active.",
                        "is_active": "false",
                    }
                    raise APIException206(
                        detail=msg,
                    )

                payload = jwt_payload_handler(user)
                user_logged_in.send(
                    sender=user.__class__, request=self.context, user=user
                )

                # Serialize user object to make it JSON serializable
                user_data = UserSerializer(user, context=self.context).data
                return {"data": {"token": jwt_encode_handler(payload), "user": user_data}}
            else:
                user = check_user(email, None, False)
                if user and not user.verify_email:
                    msg = {
                        "message": "User account email verification not completed",
                        "email_verified": "false",
                    }
                    raise APIException206(
                        detail=msg,
                    )
                if user and not user.is_active:
                    msg = {
                        "message": "User account is not active.",
                        "is_active": "false",
                    }
                    raise APIException206(
                        detail=msg,
                    )
                msg = {"message": "Unable to login with provided credential"}
                raise APIException206(
                    detail=msg,
                )
        else:
            msg = {"message": f'Must include "{self.username_field}" and "password".'}
            raise APIException206(
                detail=msg,
            )


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change endpoint.
    """

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=5)


class UserBasicProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = UserBasicDetail
        fields = ["role_name", "description", "profile_color", "profile_picture"]

    def get_profile_picture(self, obj):
        if obj.profile_picture:
            return imagekitBackend.generateURL(obj.profile_picture.name)
        return None


class SignUpSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, min_length=5)
    profile_color = serializers.CharField(required=True)


class UserSerializer(serializers.ModelSerializer):
    # user_role = serializers.SerializerMethodField()
    user_detail = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    space = serializers.SerializerMethodField()
    space_invitation = serializers.SerializerMethodField()
    # profile_completed = serializers.SerializerMethodField()
    current_step = serializers.SerializerMethodField()
    organization_list = serializers.SerializerMethodField()
    active_organization = serializers.SerializerMethodField()
    active_space = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "verify_email",
            "organization_list",
            "full_name",
            "user_detail",
            "organization",
            "space",
            "space_invitation",
            "user_token",
            "current_step",
            "active_organization",
            "active_space",
        ]

    def get_user_role(self, obj):
        user_role = None
        try:
            user_role = obj.userroles_user
        except ObjectDoesNotExist:
            return "User".lower()
        if user_role and user_role.role:
            return user_role.role.code.lower()
        return "User".lower()

    def get_user_detail(self, obj):
        if hasattr(obj, "userbasicdetail_user"):
            user_obj = obj.userbasicdetail_user
            if user_obj:
                return UserBasicProfileSerializer(user_obj).data
        return {}

    # def get_profile_completed(self, obj):
    #     if hasattr(obj, 'userbasicdetail_user'):
    #         return True
    #     return False

    def get_current_step(self, obj):
        if not hasattr(obj, "userbasicdetail_user"):
            return "profile"
        elif not obj.organization:
            return "organization"
        # elif not obj.organization.seeking:
        #     return 'seeking'
        # elif not obj.organization.tags:
        #     return 'tags'
        return "completed"

    def get_organization(self, obj):
        if obj.organization and obj.organization.status == "active":
            return SpaceOrganizationSerializers(obj.organization).data
        return {}

    def get_active_organization(self, obj):
        if hasattr(obj, "userbasicdetail_user"):
            user_obj = obj.userbasicdetail_user
            if (
                user_obj
                and user_obj.active_organization
                and user_obj.active_organization.status == "active"
            ):
                return SpaceOrganizationSerializers(user_obj.active_organization).data
        return {}

    def get_active_space(self, obj):
        if hasattr(obj, "userbasicdetail_user"):
            user_obj = obj.userbasicdetail_user
            if (
                user_obj
                and user_obj.active_space
                and user_obj.active_space.status == "active"
            ):
                return user_obj.active_space.to_json(SPACE_LIST_ALL)

            # else:
            #     default_space = (
            #         user_obj.active_organization.space_space_organization.filter(
            #             is_default=True, status="active"
            #         ).first()
            #     )
            #     if default_space:
            #         user_obj.active_space = default_space
            #         user_obj.save()
            #         return default_space.to_json(SPACE_LIST_ALL)

        return {}

    def get_space(self, obj):
        from unpod.space.models import SpaceMemberRoles

        space_list = []
        space_objs = SpaceMemberRoles.objects.filter(
            user=obj, space__status="active"
        ).select_related("space", "role")
        for space in space_objs:
            space_list.append(
                {
                    "name": space.space.name,
                    "description": space.space.description,
                    "role": space.role.role_code,
                    "token": space.space.token,
                }
            )
        return space_list

    def get_space_invitation(self, obj):
        from unpod.space.services import get_space_invitation_data

        return get_space_invitation_data(obj.email)

    def get_organization_list(self, obj):
        from unpod.space.models import OrganizationMemberRoles

        org_list = []
        org_fields = [
            "organization__name",
            "role__role_code",
            "organization__token",
            "organization__is_private_domain",
            "organization__domain",
            "organization__domain_handle",
            "organization__account_type__slug",
            "organization__pilot__handle",
            "organization__color",
            "organization__logo",
        ]
        organization_list_obj = (
            OrganizationMemberRoles.objects.filter(
                user=obj, organization__status="active"
            )
            .select_related("organization", "role")
            .values(*org_fields)
        )
        for org in organization_list_obj:
            org_list.append(
                {
                    "name": org["organization__name"],
                    "role": org["role__role_code"],
                    "token": org["organization__token"],
                    "is_private_domain": org["organization__is_private_domain"],
                    "domain_handle": org["organization__domain_handle"],
                    "account_type": org["organization__account_type__slug"],
                    "domain": org["organization__domain"],
                    "pilot_handle": org["organization__pilot__handle"],
                    "color": org["organization__color"],
                    "logo": imagekitBackend.generateURL(org["organization__logo"]),
                }
            )
        return org_list

    def check_org(self, instance):
        check_dt = timezone.now() - timezone.timedelta(days=1)
        org_invite = OrganizationInvite.objects.filter(
            user_email=instance.email,
            invite_verified=True,
            invite_verify_dt__gt=check_dt,
        ).first()
        if org_invite:
            domain, org = org_invite.organization.domain_handle, org_invite.organization
            org = org.to_json(
                [
                    "name",
                    "token",
                    "domain",
                    "domain_handle",
                    "is_private_domain",
                    "logo",
                ]
            )
            if org["logo"]:
                org["logo"] = imagekitBackend.generateURL(org["logo"].name)
                org["invite_token"] = org_invite.invite_token
            else:
                org["logo"] = None
            return org
        domain, org = checkUserOragaization(instance)
        if org:
            return org
        return None

    def check_space(self, instance):
        check_dt = timezone.now() - timezone.timedelta(days=1)
        space_invite = SpaceInvite.objects.filter(
            user_email=instance.email,
            invite_verified=True,
            invite_verify_dt__gt=check_dt,
        ).first()
        if space_invite:
            space = SpaceListSerializers(space_invite.space).data
            space["invite_token"] = space_invite.invite_token
            return space
        return None

    def to_representation(self, instance):
        user = instance
        instance = super().to_representation(instance)
        if instance["organization"]:
            instance["is_private_domain"] = instance["organization"][
                "is_private_domain"
            ]
        else:
            instance["is_private_domain"] = validate_email_type(instance["email"])
            check_org = self.check_org(user)
            if check_org:
                instance["current_step"] = "join_organization"
                instance["organization"] = check_org
                instance["invite_type"] = "organization"
            else:
                check_space = self.check_space(user)
                if check_space:
                    instance["current_step"] = "join_space"
                    instance["space"] = check_space
                    instance["invite_type"] = "space"
        instance["domain"] = fetch_email_domain(instance["email"])
        return instance


class UserUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(write_only=True, required=False)
    last_name = serializers.CharField(write_only=True, required=False)
    role_name = serializers.CharField(write_only=True, required=False)
    description = serializers.CharField(
        write_only=True, required=False, allow_blank=True, allow_null=True
    )
    profile_color = serializers.CharField(
        write_only=True, required=False, max_length=20
    )
    profile_picture = RestrictedFileField(
        write_only=True,
        required=False,
        content_types=["image/png", "image/jpeg"],
        max_upload_size=1048576,
    )


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True, validators=[UniqueValidator(queryset=User.objects.all())]
    )

    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )

    class Meta:
        model = User
        fields = (
            "password",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "id",
            "change_password",
        )
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
        }


class UserInviteTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInviteToken
        fields = "__all__"


class UserAdminListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "email",
            "full_name",
            "date_joined",
            "is_active",
            "user_token",
            "verify_email",
        ]

    def create_login_token(self, user):
        if not user.verify_email:
            msg = {"message": "User account email verification not completed"}
            raise APIException206(
                detail=msg,
            )
        if not user.is_active:
            msg = {"message": "User account is not active."}
            raise APIException206(
                detail=msg,
            )
        payload = jwt_payload_handler(user)
        payload["exp"] = datetime.utcnow() + timedelta(days=1)
        return jwt_encode_handler(payload)


class UserDeviceInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDevice
        fields = "__all__"


class UserDeviceSerializer(serializers.Serializer):
    device_id = serializers.CharField(required=True)
    is_active = serializers.BooleanField(required=False)
    fcm_token = serializers.CharField(required=True)
    device_type = serializers.CharField(required=True)
    device_model = serializers.CharField(required=False, allow_blank=True)
    language = serializers.CharField(required=False, allow_blank=True)
    timezone = serializers.CharField(required=False, allow_blank=True)
    ip_address = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True)
    app_version = serializers.CharField(required=True)
    os_version = serializers.CharField(required=True)

    class Meta:
        model = UserDevice

        fields = [
            "device_id",
            "is_active",
            "fcm_token",
            "device_type",
            "device_model",
            "language",
            "timezone",
            "ip_address",
            "location",
            "app_version",
            "os_version",
        ]

    def create(self, validated_data):
        return UserDevice.objects.create(**validated_data)


class AuthTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token

        fields = ["key", "user", "created"]
