from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin
from unpod.common.mixin import UnpodCustomModelAdmin
from unpod.space.models import (
    OrganizationAccessRequest,
    OrganizationInvite,
    SpaceAccessRequest,
    SpaceInvite,
    Space,
    SpaceMemberRoles,
    SpaceOrganization,
    OrganizationMemberRoles,
    SpaceOrganizationBillingInfo,
)


# Register your models here.


# fmt: off
@admin.register(Space)
class SpaceAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ["name", "token", "space_type","space_organization", "slug", "content_type", "privacy_type", 'is_default', 'status']
    list_filter = ['privacy_type', 'is_default', 'status', "space_type", 'space_organization']
    search_fields = ["name", "slug", "token", "space_organization__name", "space_organization__token"]


@admin.register(SpaceOrganization)
class SpaceOrganizationAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = [
        "name",
        "token",
        'domain_handle',
        'domain',
        'account_type',
        'privacy_type',
        'is_private_domain',
        "org_type",
        'status'
    ]
    search_fields = ["name", "token"]
    list_filter = ['is_private_domain', 'account_type', 'privacy_type', 'status', "org_type"]


@admin.register(OrganizationInvite)
class OrganizationInviteAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ["organization", "role", "invite_by", "invite_token",
                    "user_email", "valid_upto", "invite_verified", "is_joined"]
    list_filter = ["invite_verified", "is_joined", 'role', "organization"]
    search_fields = [
        "invite_by__first_name",
        "invite_by__last_name",
        "organization__name",
        "invite_token",
        "role__role_name",
        "user_email"
    ]


@admin.register(OrganizationAccessRequest)
class OrganizationAccessRequestViewAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = [
        "organization",
        "user", "role",
        "request_type",
        "request_token",
        "request_verified",
        "is_expired",
        "is_joined"
    ]
    list_filter = ['request_verified', "is_expired", "is_joined"]
    search_fields = ['request_token', 'organization__name', 'user__first_name', 'user__last_name', 'role__role_name']


@admin.register(SpaceMemberRoles)
class SpaceMemberRolesAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ["user", "space", "role", "grant_by"]
    list_filter = ['role']
    search_fields = [
        "user__first_name",
        "user__last_name",
        "space__name",
        "space__token",
        "space__space_organization__name",
        "role__role_name"
    ]


@admin.register(OrganizationMemberRoles)
class OrganizationMemberRolesAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ["user", "organization", "role", "grant_by"]
    list_filter = ['role']
    search_fields = ["user__first_name", "user__last_name", "organization__name", "role__role_name"]


@admin.register(SpaceInvite)
class SpaceInviteAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ["space", "role", "invite_by", "invite_token",
                    "user_email", "valid_upto", "invite_verified", "is_joined"]
    list_filter = ["invite_verified", "is_joined", 'role']
    search_fields = ["user__first_name", "user__last_name", "space__name", "invite_token"]


@admin.register(SpaceAccessRequest)
class SpaceAccessRequestViewAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = [
        "space",
        "user",
        "role",
        "request_type",
        "request_token",
        "request_verified",
        "is_expired",
        "is_joined"
    ]
    list_filter = ['request_verified', "is_expired", "is_joined"]
    search_fields = ['request_token', 'space__name', 'user__first_name', 'user__last_name', 'role__role_name']


@admin.register(SpaceOrganizationBillingInfo)
class SpaceOrganizationBillingInfoAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = [
        "organization",
        "contact_person",
        "city",
        "country",
        "default",
        "updated_at"
    ]
    list_filter = ["default", "country", "updated_at"]
    search_fields = [
        "organization__name",
        "contact_person",
        "city",
        "emails",
        "tax_ids"
    ]
    readonly_fields = ["created_at", "updated_at"]
