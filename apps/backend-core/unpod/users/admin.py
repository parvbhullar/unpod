from django.contrib import admin
from django.contrib.auth import admin as auth_admin, get_user_model
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportActionModelAdmin

from unpod.common.mixin import UnpodCustomModelAdmin
from unpod.users.forms import UserChangeForm, UserCreationForm
from unpod.users.models import (
    BlackListToken,
    UserBasicDetail,
    UserInviteToken,
    Roles,
    UserRoles,
    UserDevice,
)

User = get_user_model()


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    # Django 5.0+ adds usable_password to add_fieldsets by default,
    # but we need to exclude it for our custom User model
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2"),
            },
        ),
    )
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            _("Personal info"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "phone_number",
                    "mode",
                    "user_token",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "verify_email",
                    "verify_mob",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    list_display = [
        "id",
        "username",
        "email",
        "first_name",
        "last_name",
        "phone_number",
        "user_token",
        "referrer_code",
        "mode",
        "created",
        "is_superuser",
    ]
    search_fields = ["email", "username", "user_token"]


@admin.register(UserInviteToken)
class EmailAdmin(UnpodCustomModelAdmin):
    list_display = [
        "invited_by_user",
        "user_email",
        "invite_token",
        "valid_time",
        "success",
        "verify",
    ]
    list_filter = ["success", "verify"]


@admin.register(Roles)
class RolesAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    list_display = ["name", "role_type"]


@admin.register(UserRoles)
class UserRolesAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ["user", "role"]
    list_filter = ["role"]


@admin.register(UserBasicDetail)
class UserBasicDetailAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ["user", "role_name", "profile_color", "active_organization"]


@admin.register(BlackListToken)
class BlackListTokenAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    list_display = ["id", "user_id", "token"]


@admin.register(UserDevice)
class UserDeviceAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = [
        "id",
        "user",
        "device_id",
        "device_type",
        "device_model",
        "created_at",
    ]
    list_filter = ["device_type", "is_active"]
    search_fields = ["user__username", "device_id"]
