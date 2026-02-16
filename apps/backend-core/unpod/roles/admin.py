from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin
from unpod.common.mixin import UnpodCustomModelAdmin

from unpod.roles.models import AccountTags, Roles


@admin.register(Roles)
class SpaceRolesAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):

    list_display = ["role_name", "role_code", 'role_type', "is_default"]
    list_filter = ['is_default', 'role_type']
    search_fields = ["role_name", "role_code"]


@admin.register(AccountTags)
class AccountTagsAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ["name", "slug", "description", 'tag_type', 'parent', 'is_active']
    list_filter = ['tag_type', 'is_active']
    search_fields = ["name", "slug"]
