from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin
from unpod.channels.models import (
    AppConnectorConfig,
    App,
    AppConnectRequest,
    AppConfigLink,
)
from unpod.common.mixin import (
    SoftDeletedModelAdmin,
    UnpodCustomModelAdmin,
    createProxyModelAdmin,
)


@admin.register(App)
class AppAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    list_display = ["name", "description", "is_active", "icon", "slug"]
    list_filter = ["is_active"]


@admin.register(AppConnectorConfig)
class AppConnectorConfigAdmin(ImportExportActionModelAdmin, admin.ModelAdmin):
    list_display = ["organization", "user", "app", "state", "connected_email"]
    list_filter = ["organization", "user"]

    def connected_email(self, obj):
        return obj.configuration.get("email", "")


class AppConnectorConfigDeletedAdmin(
    ImportExportActionModelAdmin, UnpodCustomModelAdmin, SoftDeletedModelAdmin
):
    list_display = ["organization", "user", "app", "state", "connected_email"]
    list_filter = ["organization", "user"]

    def connected_email(self, obj):
        return obj.configuration.get("email", "")


createProxyModelAdmin(
    AppConnectorConfigDeletedAdmin,
    AppConnectorConfig,
    name="AppConnectorConfigDeletedAdmin",
)


# register AppConnectRequest
@admin.register(AppConnectRequest)
class AppConnectRequestAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ["user", "app", "request_id", "config"]
    list_filter = ["app"]


@admin.register(AppConfigLink)
class PilotLinkAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ["user", "content_type", "app_config", "content_object"]
    list_filter = ["content_type"]
