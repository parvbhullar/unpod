from django.urls import path
from unpod.core_components.views import GlobalInvitationViewSet

from unpod.space.views import (
    # OrganizationPermissionViewSet,
    RolesViewSet,
    SpaceInviteViewSet,
    # SpaceOrganizationViewSet,
    SpaceViewSet,
    SpaceAccessRequestViewSet,
    SubscribeViewSet, SpaceMongoDBViewSet,
)

app_name = "space_v1"

urlpatterns = [
    path("", SpaceViewSet.as_view({"post": "create", "get": "list"}), name="space"),
    path(
        "<str:space_slug>/",
        SpaceViewSet.as_view(
            {"get": "space_detail", "put": "update_space", "delete": "archive_space"}
        ),
        name="space",
    ),
    path(
        "<str:space_slug>/analytics/",
        SpaceViewSet.as_view({"get": "get_space_analytics"}),
        name="space-analytics",
    ),
    path(
        "<str:space_slug>/schema-download/",
        SpaceViewSet.as_view({"get": "download_schema"}),
        name="space_download_schema",
    ),
    # path('invite/', SpaceInviteViewSet.as_view({'post': 'create'}), name='invite-create'),
    # path('organization/create/', SpaceOrganizationViewSet.as_view({'post': 'create'}), name='organization'),
    # path('organization/check/', SpaceOrganizationViewSet.as_view({'get': 'check'}), name='organization'),
    # path('organization/action/', SpaceOrganizationViewSet.as_view({'put': 'action'}), name='organization'),
    # path('organization/detail/<str:domain_handle>/', SpaceOrganizationViewSet.as_view({'get': 'get_organization_detail'}), name='organization'),
    # path('organization/update/<str:domain_handle>/', SpaceOrganizationViewSet.as_view({'put': 'update_organization'}), name='organization'),
    path(
        "subscribe/trending/",
        SubscribeViewSet.as_view({"get": "get_trending"}),
        name="subscription-trending",
    ),
    path(
        "subscribe/join/<str:space_slug>/",
        SubscribeViewSet.as_view({"get": "join_subscribe"}),
        name="subscription-join",
    ),
    path(
        "subscribe/leave/<str:space_slug>/",
        SubscribeViewSet.as_view({"get": "leave_subscribe"}),
        name="subscription-leave",
    ),
    path(
        "invite/verify/",
        GlobalInvitationViewSet.as_view({"post": "inviteVerify"}),
        name="invite-verify",
    ),
    path(
        "invite/join/<str:token>/",
        SpaceInviteViewSet.as_view({"get": "inviteJoin"}),
        name="invite-join",
    ),
    path(
        "invite/resend/<str:token>/",
        SpaceInviteViewSet.as_view({"get": "inviteResend"}),
        name="invite-resend",
    ),
    path(
        "invite/cancel/<str:token>/",
        SpaceInviteViewSet.as_view({"delete": "inviteCancel"}),
        name="invite-cancel",
    ),
    path(
        "invite/pending/",
        SpaceInviteViewSet.as_view({"get": "userInvitePending"}),
        name="user-invite-pending",
    ),
    path(
        "<str:token>/invite/",
        RolesViewSet.as_view({"post": "createInvite"}),
        name="space-invite",
    ),
    path(
        "invite/<str:token>/",
        SpaceInviteViewSet.as_view({"delete": "deleteInvite", "put": "updateInvite"}),
        name="space-invite-delete",
    ),
    # path('organization/permission/<str:domain_handle>/', OrganizationPermissionViewSet.as_view(
    #     {
    #         'post': 'create',
    #         'put': 'permission_update',
    #         'delete': 'permission_delete'
    #     }), name='organization'),
    # path('organization/invite/<str:token>/', OrganizationPermissionViewSet.as_view({'delete': 'deleteInvite', 'put':'updateInvite'}), name='space-invite-delete'),
    # path('organization/join/<str:token>/', OrganizationPermissionViewSet.as_view({'get': 'join'}), name='join-organization'),
    path(
        "<str:token>/permission/",
        RolesViewSet.as_view(
            {
                "post": "createInvite",
                "put": "permission_update",
                "delete": "permission_delete",
            }
        ),
        name="space-permission",
    ),
    path(
        "<str:token>/ownership-transfer/",
        RolesViewSet.as_view({"get": "ownership_transfer"}),
        name="ownership-transfer",
    ),
    path(
        "<str:space_slug>/request/",
        SpaceAccessRequestViewSet.as_view({"get": "request_add"}),
        name="space_request_add",
    ),
    path(
        "<str:space_slug>/request/change-role/",
        SpaceAccessRequestViewSet.as_view({"post": "request_change_role"}),
        name="space_request_change_role",
    ),
    path(
        "<str:space_slug>/request/<str:request_token>/",
        SpaceAccessRequestViewSet.as_view(
            {
                "get": "request_accept",
                "put": "request_update",
                "delete": "request_delete",
            }
        ),
        name="space_request",
    ),
    path(
        "<str:space_slug>/request/<str:request_token>/accept-change-role/",
        SpaceAccessRequestViewSet.as_view({"get": "accept_change_role_request"}),
        name="space_accept_change_role_request",
    ),
    path(
        "<str:space_slug>/request/<str:request_token>/reject/",
        SpaceAccessRequestViewSet.as_view({"get": "request_reject"}),
        name="space_request_reject",
    ),
    path(
        "<str:space_slug>/request/<str:request_token>/resend/",
        SpaceAccessRequestViewSet.as_view({"get": "request_resend"}),
        name="space_request_resend",
    ),

    # mongodb data
    path(
        "<str:space_slug>/calls/",
        SpaceMongoDBViewSet.as_view({"get": "get_calls"}),
        name="calls",
    ),
    path(
        "<str:space_slug>/calls/<str:task_id>/",
        SpaceMongoDBViewSet.as_view({"get": "get_call_details"}),
        name="calls",
    ),
]
