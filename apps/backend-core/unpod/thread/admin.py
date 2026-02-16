from django.contrib import admin
from unpod.thread.models import (
    PostBlockList,
    PostCommunicationActivity,
    PostCreationCronModel,
    PostInvite,
    PostReport,
    PostSessionRecording,
    ThreadPost,
    ThreadPostAccessRequest,
    ThreadPostPermission,
    ThreadPostReaction,
    ThreadPostView,
    PostCronResultModel,
)
from import_export.admin import ImportExportActionModelAdmin
from unpod.common.mixin import (
    SoftDeletedModelAdmin,
    UnpodCustomModelAdmin,
    createProxyModelAdmin,
)

# fmt:off
@admin.register(ThreadPost)
class ThreadPostAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):

    list_display = ["post_id", "space", 'privacy_type', "post_status",
                    'post_rel', 'post_type','content_type','tags', "main_post", 'parent', "slug", "seq_number"]
    list_filter = ['privacy_type', 'post_status', 'post_rel', 'post_type','content_type']
    search_fields = ["post_id", "slug", "tags", "content", "space__name", "space__token"]


class ThreadPostDeletedAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin, SoftDeletedModelAdmin):

    list_display = ["post_id", "space", 'privacy_type', "post_status",
                    'post_rel', 'tags', "main_post", "slug", "seq_number"]
    list_filter = ['privacy_type', 'post_status']


createProxyModelAdmin(ThreadPostDeletedAdmin, ThreadPost, name='ThreadPostDeletedAdmin')


@admin.register(ThreadPostPermission)
class ThreadPostPermissionAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):

    list_display = ["post", "user", "role"]
    list_filter = ['role', 'user']


@admin.register(ThreadPostReaction)
class ThreadPostReactionAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):

    list_display = ["post", "user", "reaction_type", "object_type", "reaction_at", "reaction_count"]
    list_filter = ['object_type']


@admin.register(ThreadPostView)
class ThreadPostViewAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):

    list_display = ["post", "user_id", "view_at"]


@admin.register(ThreadPostAccessRequest)
class ThreadPostAccessRequestViewAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):

    list_display = ["post", "user", "role", "request_token", "request_verified", "is_expired"]
    list_filter = ['request_verified', "is_expired", 'role', 'user']


@admin.register(PostInvite)
class PostInviteAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ["post", "role", "invite_by", "invite_token",
                    "user_email", "valid_upto", "invite_verified", "is_joined"]
    list_filter = ["invite_verified", "is_joined", 'role', "post"]
    search_fields = ["user", "post", "invite_token"]


@admin.register(PostReport)
class PostReportAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):

    list_display = ["post", "user", "category", "message"]
    list_filter = ["category"]


@admin.register(PostBlockList)
class PostBlockListAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):

    list_display = ["post", "user", "created"]


@admin.register(PostCommunicationActivity)
class PostCommunicationActivityAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):

    list_display = ["post", "user", "channel_name", "start_dt", "end_dt", "live_status"]
    search_fields = ["channel_name"]

@admin.register(PostSessionRecording)
class PostSessionRecordingAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):

    list_display = ["session", "recording_status", "agora_sid", "post_created", 'recording_video_status']
    list_filter = ['recording_status', 'recording_video_status', 'post_created']


@admin.register(PostCreationCronModel)
class PostCreationCronModelAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):

    list_display = ["user_id", "space_token", "title", "content", "post_id", 'post_created', "success"]
    list_filter = ["user_id", "space_token", "post_created", "success", "privacy_type"]

    search_fields = ["title", "content", "post_id"]

    def get_content(self, obj):
        return obj.content[:100]


@admin.register(PostCronResultModel)
class PostCronResultModelAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):

    list_display = ["post_id", 'post_created', "success", "message"]
    list_filter = ["post_created", "success",]

    search_fields = ["post_id"]
