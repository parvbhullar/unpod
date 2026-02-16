from django.db.models import F
from rest_framework import serializers
from unpod.common.constants import DATETIME_FORMAT
from unpod.common.decorators import checkUserReturnDefault
from unpod.common.helpers.validation_helper import validate_domain
from unpod.common.serializer import RestrictedFileField
from unpod.common.storage_backends import imagekitBackend
from unpod.roles.constants import (
    DEFAULT_ORGANIZATION_PERMISSION_ROLE,
    DEFAULT_SPACE_PERMISSION_ROLE,
)
from unpod.roles.services import generateRefObject, getUserFinalRole
from unpod.roles.utlis import getRoleBasedOperation
from unpod.common.enum import SpaceType, KnowledgeBaseContentType
from unpod.space.constants import SPACE_LIST_ALL, SPACE_LIST_FIELDS
from unpod.space.models import Space, SpaceOrganization, SpaceOrganizationBillingInfo
from unpod.space.utils import get_space_access_request, get_organization_access_request


class SpaceRolePermissionCreateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    role_code = serializers.ChoiceField(choices=["viewer", "editor"], required=True)


class SpaceAccessRequestUpdateSerializer(serializers.Serializer):
    role_code = serializers.ChoiceField(choices=["viewer", "editor"], required=True)


class SpaceCreateSerializers(serializers.Serializer):
    name = serializers.CharField(required=True, max_length=30)
    description = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    invite_list = SpaceRolePermissionCreateSerializer(many=True, required=False)
    privacy_type = serializers.ChoiceField(
        choices=["private", "shared", "public"], required=False
    )
    space_type = serializers.ChoiceField(
        choices=SpaceType.choices(), default=SpaceType.general.name, required=False
    )
    content_type = serializers.ChoiceField(
        choices=KnowledgeBaseContentType.choices(),
        default=KnowledgeBaseContentType.general.name,
        required=False,
    )

    schema = serializers.JSONField(required=False)

    files = serializers.ListField(
        child=serializers.FileField(
            max_length=100000, allow_empty_file=False, use_url=False
        ),
        required=False,
    )


class SpaceUpdateSerializers(serializers.Serializer):
    name = serializers.CharField(required=False, max_length=30)
    description = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    logo = RestrictedFileField(
        write_only=True,
        required=False,
        content_types=["image/png", "image/jpeg"],
        max_upload_size=1048576,
    )
    privacy_type = serializers.ChoiceField(
        choices=["private", "shared", "public"], required=False
    )

    schema = serializers.JSONField(required=False)


class SpaceOrganizationSerializers(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    account_type = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    seeking = serializers.SlugRelatedField(slug_field="slug", many=True, read_only=True)
    tags = serializers.SlugRelatedField(slug_field="slug", many=True, read_only=True)
    org_id = serializers.SerializerMethodField()
    pilot_handle = serializers.CharField(source="pilot.handle", read_only=True)

    class Meta:
        model = SpaceOrganization
        exclude = ["id", "created_by", "updated_by"]

    def get_logo(self, obj):
        if obj.logo:
            return imagekitBackend.generateURL(obj.logo.name)
        return None

    def to_representation(self, instance):
        instance = super().to_representation(instance)
        return instance

    def get_org_id(self, obj):
        return obj.id


class SpaceOrgDetailSerializers(SpaceOrganizationSerializers):
    users = serializers.SerializerMethodField()
    billing_info = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    access_request = serializers.SerializerMethodField()

    @checkUserReturnDefault([])
    def get_users(self, obj):
        users = obj.organizationmemberroles_organization.select_related(
            "user", "role", "user__userbasicdetail_user"
        )
        users_data = []
        for user in users:
            if user.user:
                user_data = {
                    "email": user.user.email,
                    "full_name": user.user.full_name,
                    "role": user.role.role_code,
                    "join_date": user.created.strftime(DATETIME_FORMAT),
                    "joined": True,
                }
                if hasattr(user.user, "userbasicdetail_user"):
                    user_data[
                        "profile_color"
                    ] = user.user.userbasicdetail_user.profile_color
                if hasattr(user.user, "userbasicdetail_user"):
                    if user.user.userbasicdetail_user.profile_picture:
                        user_data["profile_picture"] = imagekitBackend.generateURL(
                            user.user.userbasicdetail_user.profile_picture.name
                        )
                users_data.append(user_data)
        pending_invite = obj.organizationinvite_organization.filter(
            is_joined=False, expired=False
        )
        for user in pending_invite:
            users_data.append(
                {
                    "email": user.user_email,
                    "full_name": "",
                    "role": user.role.role_code,
                    "joined": False,
                    "invite_token": user.invite_token,
                    "invite_verified": user.invite_verified,
                }
            )
        return users_data

    @checkUserReturnDefault(DEFAULT_ORGANIZATION_PERMISSION_ROLE)
    def get_user_role(self, obj):
        user = getattr(self.context.get("request"), "user", None) or self.context.get(
            "user"
        )
        role = (
            obj.organizationmemberroles_organization.filter(user=user)
            .select_related("role")
            .first()
        )
        if role:
            return role.role.role_code
        return DEFAULT_ORGANIZATION_PERMISSION_ROLE

    @checkUserReturnDefault([])
    def get_access_request(self, obj):
        return get_organization_access_request(obj)

    def get_billing_info(self, obj):
        billing_info = SpaceOrganizationBillingInfo.objects.filter(
            organization=obj, default=True
        ).first()

        if not billing_info:
            billing_info = SpaceOrganizationBillingInfo.objects.create(
                organization=obj,
                default=True,
            )

        return BillingInfoRetrieveSerializer(billing_info).data

    @checkUserReturnDefault({"joined": False, "role_code": DEFAULT_ORGANIZATION_PERMISSION_ROLE})
    def get_joined(self, instance, users):
        user = getattr(self.context.get("request"), "user", None) or self.context.get(
            "user"
        )
        email = user.email
        for user in users:
            if user["email"] == email and user["joined"]:
                return {"joined": True, "role_code": user["role"]}
        return {"joined": False, "role_code": DEFAULT_ORGANIZATION_PERMISSION_ROLE}

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        role_data = self.get_joined(instance, representation["users"])
        representation["joined"] = role_data["joined"]
        representation["user_role"] = role_data["role_code"]
        representation["final_role"] = role_data["role_code"]
        representation["allowed_operations"] = getRoleBasedOperation(
            role_data["role_code"], "organization"
        )

        return representation


class SpaceDetailSerializers(serializers.ModelSerializer):
    organization = serializers.SerializerMethodField()
    users = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    access_request = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()
    pilots = serializers.SerializerMethodField()
    schema = serializers.JSONField(
        read_only=True, source="knowledgebaseconfig.schema", default={}
    )

    class Meta:
        model = Space
        fields = [
            "name",
            "slug",
            "token",
            "privacy_type",
            "description",
            "logo",
            "organization",
            "users",
            "user_role",
            "access_request",
            "space_type",
            "content_type",
            "schema",
            "pilots",
        ]

    def get_pilots(self, obj):
        # Import here to avoid circular imports
        from unpod.core_components.models import Pilot

        # Get pilots linked to this space
        pilots = Pilot.objects.filter(space=obj)
        if not pilots.exists():
            return []
        # Return basic info about each pilot
        return [
            {
                "id": pilot.id,
                "name": pilot.name,
                "handle": pilot.handle,
                "type": pilot.type,
                "description": pilot.description,
            }
            for pilot in pilots
        ]

    def get_organization(self, obj):
        space_organization = obj.space_organization
        return SpaceOrganizationSerializers(space_organization).data

    @checkUserReturnDefault([])
    def get_users(self, obj):
        users = obj.spacememberroles_space.all().select_related(
            "user", "role", "user__userbasicdetail_user"
        )
        users_data = []
        for user in users:
            user_data = {
                "token": user.user.user_token,
                "email": user.user.email,
                "full_name": user.user.full_name,
                "role": user.role.role_code,
                "join_date": user.created.strftime(DATETIME_FORMAT),
                "joined": True,
            }
            if hasattr(user.user, "userbasicdetail_user"):
                user_data[
                    "profile_color"
                ] = user.user.userbasicdetail_user.profile_color
            if hasattr(user.user, "userbasicdetail_user"):
                if user.user.userbasicdetail_user.profile_picture:
                    user_data["profile_picture"] = imagekitBackend.generateURL(
                        user.user.userbasicdetail_user.profile_picture.name
                    )
            users_data.append(user_data)
        pending_invite = obj.spaceinvite_space.filter(is_joined=False, expired=False)
        for user in pending_invite:
            users_data.append(
                {
                    "email": user.user_email,
                    "full_name": "",
                    "role": user.role.role_code,
                    "joined": False,
                    "invite_token": user.invite_token,
                    "invite_verified": user.invite_verified,
                }
            )
        return users_data

    @checkUserReturnDefault(DEFAULT_SPACE_PERMISSION_ROLE)
    def get_user_role(self, obj):
        user = getattr(self.context.get("request"), "user", None) or self.context.get(
            "user"
        )
        role = (
            obj.spacememberroles_space.filter(user=user).select_related("role").first()
        )
        if role:
            return role.role.role_code
        return DEFAULT_SPACE_PERMISSION_ROLE

    @checkUserReturnDefault([])
    def get_access_request(self, obj):
        return get_space_access_request(obj)

    def get_logo(self, obj):
        if obj.logo:
            return imagekitBackend.generateURL(obj.logo.name)
        return None

    @checkUserReturnDefault(False)
    def get_joined(self, instance, users):
        user = getattr(self.context.get("request"), "user", None) or self.context.get(
            "user"
        )
        email = user.email
        for user in users:
            if user["email"] == email and user["joined"]:
                return True
        return False

    def to_representation(self, instance):
        user = getattr(self.context.get("request"), "user", None) or self.context.get(
            "user"
        )
        representation = super().to_representation(instance)
        representation["joined"] = self.get_joined(instance, representation["users"])
        ref_dict = generateRefObject("space", instance)
        ref_dict["id"] = instance.id
        final_role = (
            getUserFinalRole(user, "space", ref_dict) or DEFAULT_SPACE_PERMISSION_ROLE
        )
        if final_role != "owner":
            final_role = representation["user_role"]
        representation["final_role"] = final_role
        representation["allowed_operations"] = getRoleBasedOperation(
            final_role, "space"
        )
        representation["connected_apps"] = instance.app_configs.annotate(
            app_name=F("app_config__app__name"),
            app_slug=F("app_config__app__slug"),
            app_state=F("app_config__state"),
            app_description=F("app_config__app__description"),
            app_logo=F("app_config__app__icon"),
        ).values(
            "id",
            "app_name",
            "app_slug",
            "app_state",
            "link_config",
            "app_description",
            "app_logo",
        )

        for app in representation["connected_apps"]:
            app["app_logo"] = (
                imagekitBackend.generateURL(app["app_logo"])
                if app["app_logo"]
                else None
            )
        return representation


class SpaceListSerializers(serializers.ModelSerializer):
    organization = serializers.SerializerMethodField()
    schema = serializers.JSONField(
        read_only=True, source="knowledgebaseconfig.schema", default={}
    )
    pilots = serializers.SerializerMethodField()

    class Meta:
        model = Space
        fields = [*SPACE_LIST_FIELDS, "organization", "schema", "pilots"]

    def get_organization(self, obj):
        space_organization = obj.space_organization
        return SpaceOrganizationSerializers(space_organization).data

    def get_pilots(self, obj):
        # Import here to avoid circular imports
        from unpod.core_components.models import Pilot

        # Get pilots linked to this space
        pilots = Pilot.objects.filter(space=obj)
        if not pilots.exists():
            return []

        # Return basic info about each pilot
        return [
            {
                "id": pilot.id,
                "name": pilot.name,
                "handle": pilot.handle,
                "type": pilot.type,
                "description": pilot.description,
            }
            for pilot in pilots
        ]


class SpaceListAllSerializers(serializers.ModelSerializer):
    class Meta:
        model = Space
        fields = [*SPACE_LIST_ALL]


class SpaceOrganizationCreateSerializers(serializers.Serializer):
    name = serializers.CharField(required=True, max_length=100)
    domain_handle = serializers.CharField(required=True, max_length=30)
    description = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    account_type = serializers.CharField(required=True)
    color = serializers.CharField(required=True, max_length=7)
    logo = RestrictedFileField(
        write_only=True,
        required=False,
        content_types=["image/png", "image/jpeg"],
        max_upload_size=1048576,
    )
    privacy_type = serializers.ChoiceField(choices=["shared", "public"], required=False)
    region = serializers.CharField(required=False, max_length=50)

    def validate_domain_handle(self, value):
        return value


class OrgUpdateSerializers(serializers.Serializer):
    account_type = serializers.CharField(required=False)
    name = serializers.CharField(required=False, max_length=30)
    logo = RestrictedFileField(
        write_only=True,
        required=False,
        content_types=["image/png", "image/jpeg"],
        max_upload_size=1048576,
    )
    privacy_type = serializers.ChoiceField(choices=["shared", "public"], required=False)
    seeking = serializers.ListField(
        required=False, child=serializers.CharField(max_length=50)
    )
    tags = serializers.ListField(
        required=False, child=serializers.CharField(max_length=50)
    )
    region = serializers.CharField(required=False, max_length=50)


class BillingInfoRetrieveSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )

    class Meta:
        model = SpaceOrganizationBillingInfo
        fields = [
            "id",
            "organization",
            "organization_name",
            "tax_ids",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "country",
            "postal_code",
            "contact_person",
            "phone_number_cc",
            "phone_number",
            "email",
            "default",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "organization_name"]


class BillingInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpaceOrganizationBillingInfo
        fields = [
            "organization",
            "tax_ids",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "country",
            "postal_code",
            "contact_person",
            "phone_number_cc",
            "phone_number",
            "email",
            "default",
        ]
