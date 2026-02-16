from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin
from unpod.common.mixin import UnpodCustomModelAdmin
from unpod.notification.models import Notification

# Register your models here.


@admin.register(Notification)
class NotificationAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):

    list_display = ["object_type", "event", "user_to", "token", "expired", "read", "created", "modified"]
    list_filter = ['object_type', 'event', "expired", "read"]
    search_fields = ["token"]
