from django.urls import path

from .views import (
    OrganizationAccessRequestViewSet,
    OrganizationPermissionViewSet,
    SpaceOrganizationViewSet,
    OrganizationBillingInfoViewSet,
)

app_name = "space_organization_v1"

urlpatterns = [
    path(
        "",
        SpaceOrganizationViewSet.as_view({"post": "create"}),
        name="organization",
    ),
    path(
        "create/",
        SpaceOrganizationViewSet.as_view({"post": "create"}),
        name="organization",
    ),
    path(
        "check/",
        SpaceOrganizationViewSet.as_view({"get": "check"}),
        name="organization",
    ),
    path(
        "action/",
        SpaceOrganizationViewSet.as_view({"put": "action"}),
        name="organization",
    ),
    path(
        "<str:domain_handle>/",
        SpaceOrganizationViewSet.as_view({"get": "get_organization_detail", "put": "update_organization"}),
        name="organization",
    ),
    path(
        "detail/<str:domain_handle>/",
        SpaceOrganizationViewSet.as_view({"get": "get_organization_detail"}),
        name="organization",
    ),
    path(
        "update/<str:domain_handle>/",
        SpaceOrganizationViewSet.as_view({"put": "update_organization"}),
        name="organization",
    ),
    path(
        "archive/<str:domain_handle>/",
        SpaceOrganizationViewSet.as_view({"delete": "archive_organization"}),
        name="archive-organization",
    ),
    path(
        "allowed-space/<str:domain_handle>/",
        SpaceOrganizationViewSet.as_view({"get": "allowed_space"}),
        name="allowed-space",
    ),
    path(
        "<str:domain_handle>/invite/",
        OrganizationPermissionViewSet.as_view(
            {
                "post": "createInvite",
            }
        ),
        name="organization-invite",
    ),
    path(
        "invite/<str:token>/",
        OrganizationPermissionViewSet.as_view(
            {"delete": "deleteInvite", "put": "updateInvite"}
        ),
        name="space-invite-delete",
    ),
    path(
        "permission/<str:domain_handle>/",
        OrganizationPermissionViewSet.as_view(
            {
                # "post": "create",
                "put": "permission_update",
                "delete": "permission_delete",
            }
        ),
        name="organization-permission",
    ),
    path(
        "ownership-transfer/<str:domain_handle>/",
        OrganizationPermissionViewSet.as_view({"get": "ownership_transfer"}),
        name="ownership-transfer",
    ),
    path(
        "user-list/<str:domain_handle>/",
        OrganizationPermissionViewSet.as_view({"get": "fetch_user_list"}),
        name="user-list",
    ),
    path(
        "join/<str:token>/",
        OrganizationPermissionViewSet.as_view({"get": "join"}),
        name="join-organization",
    ),
    path(
        "invite/resend/<str:token>/",
        OrganizationPermissionViewSet.as_view({"get": "inviteResend"}),
        name="invite-resend",
    ),
    path(
        "subscribe/my-organization/<str:domain_handle>/",
        OrganizationPermissionViewSet.as_view({"get": "subscribe_my_organization"}),
        name="subscribe-my-organization",
    ),
    path(
        "subscribe/join/<str:domain_handle>/",
        OrganizationPermissionViewSet.as_view({"get": "subscribe_join"}),
        name="subscribe-join",
    ),
    path(
        "subscribe/leave/<str:domain_handle>/",
        OrganizationPermissionViewSet.as_view({"get": "subscribe_leave"}),
        name="subscribe-leave",
    ),
    path(
        "<str:domain_handle>/request/",
        OrganizationAccessRequestViewSet.as_view({"get": "request_add"}),
        name="organization_request_add",
    ),
    path(
        "<str:domain_handle>/request/change-role/",
        OrganizationAccessRequestViewSet.as_view({"post": "request_change_role"}),
        name="organization_request_change_role",
    ),
    path(
        "<str:domain_handle>/request/<str:request_token>/",
        OrganizationAccessRequestViewSet.as_view(
            {
                "get": "request_accept",
                "put": "request_update",
                "delete": "request_delete",
            }
        ),
        name="organization_request",
    ),
    path(
        "<str:domain_handle>/request/<str:request_token>/accept-change-role/",
        OrganizationAccessRequestViewSet.as_view({"get": "accept_change_role_request"}),
        name="organization_accept_change_role_request",
    ),
    path(
        "<str:domain_handle>/request/<str:request_token>/reject/",
        OrganizationAccessRequestViewSet.as_view({"get": "request_reject"}),
        name="organization_request_reject",
    ),
    path(
        "<str:domain_handle>/request/<str:request_token>/resend/",
        OrganizationAccessRequestViewSet.as_view({"get": "request_resend"}),
        name="organization_request_resend",
    ),
    path(
        "<str:domain_handle>/billing-info/",
        OrganizationBillingInfoViewSet.as_view({"get": "retrieve", "put": "update"}),
        name="billing-info",
    ),
]
