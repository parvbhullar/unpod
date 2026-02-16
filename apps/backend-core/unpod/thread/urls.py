from django.urls import path
from unpod.thread.views import (
    ThreadAccessRequestViewSet,
    ThreadAgoraViewSet,
    ThreadAnonymousViewSet,
    ThreadExploreViewSet,
    ThreadPostReportViewSet,
    ThreadPostViewSet,
    ThreadPostEventViewSet,
    ThreadRolesViewSet,
    ThreadSharedViewSet,
    ThreadViewSet,
    ThreadPostReplyViewSet,
    ThreadHMSViewSet,
    ThreadWebhookViewSet,
    PublicThreadViewSet
)

app_name = "thread_v1"

urlpatterns = [

    path(
        "<str:token>/",
        ThreadViewSet.as_view({"post": "create", "get": "list"}),
        name="thread",
    ),
    path(
        "pilot-threads/<str:pilot>/",
        ThreadViewSet.as_view({"get": "pilot_thread_list"}),
        name="pilot_thread_list",
    ),
    path(
        "connector-doc-data/<str:document_id>/",
        ThreadViewSet.as_view({"get": "document_thread_list"}),
        name="document_thread_list",
    ),
    path(
        "organisation-threads/<str:domain_handle>/",
        ThreadViewSet.as_view({"get": "organisation_thread_list"}),
        name="organisation_thread_list",
    ),
    path(
        "shared/me/", ThreadSharedViewSet.as_view({"get": "list"}), name="thread-shared"
    ),
    path(
        "anonymous/create/",
        ThreadAnonymousViewSet.as_view({"post": "create"}),
        name="thread-anonymous",
    ),
    path(
        "public-super/create/",
        ThreadAnonymousViewSet.as_view({"post": "public_thread_create"}),
        name="thread-public-super",
    ),
    path(
        "explore/trending/",
        ThreadExploreViewSet.as_view({"get": "list"}),
        name="thread-explore",
    ),
    path(
        "<str:post_slug>/action/",
        ThreadViewSet.as_view({"put": "update", "delete": "delete"}),
        name="thread",
    ),
    path(
        "<str:post_slug>/detail/",
        ThreadViewSet.as_view({"get": "retrieve"}),
        name="thread",
    ),
    #     path('<str:post_slug>/delete/', ThreadViewSet.as_view({"delete": "retrieve"}), name='thread'),
    path(
        "<str:post_slug>/next/",
        ThreadViewSet.as_view({"get": "thread_next"}),
        name="thread",
    ),
    path(
        "<str:post_slug>/previous/",
        ThreadViewSet.as_view({"get": "thread_previous"}),
        name="thread",
    ),
    path(
        "<str:post_slug>/subscribe/",
        ThreadViewSet.as_view({"get": "join_subscription"}),
        name="thread-subscribe",
    ),
    path(
        "<str:post_slug>/unsubscribe/",
        ThreadViewSet.as_view({"get": "unsubscribe"}),
        name="thread-unsubscribe",
    ),
    path(
        "<str:post_slug>/view/",
        ThreadPostEventViewSet.as_view({"get": "viewer"}),
        name="thread-view",
    ),
    path(
        "<str:post_slug>/reaction/",
        ThreadPostEventViewSet.as_view(
            {"put": "update_reaction", "get": "reaction_info"}
        ),
        name="thread-reaction",
    ),
    path(
        "<str:post_slug>/report/",
        ThreadPostReportViewSet.as_view({"post": "post"}),
        name="thread-report",
    ),
    path(
        "<str:post_slug>/reply/",
        ThreadPostReplyViewSet.as_view({"post": "create", "get": "list"}),
        name="thread-reply",
    ),
    path(
        "<str:post_slug>/reply/next/",
        ThreadPostReplyViewSet.as_view({"get": "reply_next"}),
        name="thread-reply-next",
    ),
    path(
        "<str:post_slug>/post/",
        ThreadPostViewSet.as_view({"post": "create", "get": "list"}),
        name="thread-post",
    ),
    path(
        "<str:post_slug>/permission/",
        ThreadRolesViewSet.as_view(
            {
                "post": "permission_add",
                "put": "permission_update",
                "delete": "permission_delete",
            }
        ),
        name="thread-permission",
    ),
    path(
        "<str:post_slug>/ownership-transfer/",
        ThreadRolesViewSet.as_view({"get": "ownership_transfer"}),
        name="ownership-transfer",
    ),
    path(
        "<str:post_slug>/request/",
        ThreadAccessRequestViewSet.as_view({"get": "request_add"}),
        name="thread-request",
    ),
    path(
        "<str:post_slug>/request/<str:request_token>/",
        ThreadAccessRequestViewSet.as_view(
            {
                "get": "request_accpet",
                "put": "request_update",
                "delete": "request_delete",
            }
        ),
        name="thread-request",
    ),
    path(
        "<str:post_slug>/request/<str:request_token>/resend/",
        ThreadAccessRequestViewSet.as_view({"get": "request_resend"}),
        name="thread-request",
    ),
    path(
        "<str:post_slug>/livesession/token/",
        ThreadAgoraViewSet.as_view({"get": "livesession_token"}),
        name="thread-livesession-token",
    ),
    path(
        "<str:post_slug>/livesession/start/",
        ThreadAgoraViewSet.as_view({"get": "livesession_start"}),
        name="thread-livesession-start",
    ),
    path(
        "<str:post_slug>/livesession/stop/",
        ThreadAgoraViewSet.as_view({"get": "livesession_stop"}),
        name="thread-livesession-stop",
    ),
    path(
        "<str:post_slug>/recording/start/",
        ThreadAgoraViewSet.as_view({"get": "recording_start"}),
        name="thread-recording-start",
    ),
    path(
        "<str:post_slug>/recording/stop/",
        ThreadAgoraViewSet.as_view({"get": "recording_stop"}),
        name="thread-recording-stop",
    ),
    path(
        "<str:post_slug>/hms/livesession/token/",
        ThreadHMSViewSet.as_view({"get": "livesession_code"}),
        name="thread-livesession-token-hms",
    ),
    path(
        "<str:post_slug>/hms/livesession/start/",
        ThreadHMSViewSet.as_view({"get": "livesession_start"}),
        name="thread-livesession-start-hms",
    ),
    path(
        "<str:post_slug>/hms/livesession/stop/",
        ThreadHMSViewSet.as_view({"get": "livesession_stop"}),
        name="thread-livesession-stop-hms",
    ),
    path(
        "<str:post_slug>/hms/recording/start/",
        ThreadHMSViewSet.as_view({"get": "recording_start"}),
        name="thread-recording-start-hms",
    ),
    path(
        "<str:post_slug>/hms/recording/stop/",
        ThreadHMSViewSet.as_view({"get": "recording_stop"}),
        name="thread-recording-stop-hms",
    ),
    path(
        "<str:post_slug>/hms/webhook/",
        ThreadWebhookViewSet.as_view({"post": "post"}),
        name="thread-webhook",
    ),

   path(
        "public/create-thread/",
        PublicThreadViewSet.as_view({"post": "create_thread"}),
        name="public-thread-create",
    ),
    path(
        "public/thread/<str:thread_id>/",
        PublicThreadViewSet.as_view({"patch": "update_thread"}),
        name="public-thread-create",
     ),
]
