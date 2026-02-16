from django.urls import path

# Import API v2 ViewSet (uses MongoDB directly via apiV2Platform/utils.py)
from unpod.apiV2Platform.views import (
    TaskServiceV2ViewSet,
    TelephonyNumbersViewSet,
    TelephonyProvidersViewSet,
    ProviderConfigurationsViewSet,
    TelephonyBridgesViewSet,
    CallLogsViewSet,
    SpaceV2ViewSet,
)

# fmt: off
urlpatterns = [
    # API v2 Platform - Fetches data directly from MongoDB
    # Uses TaskServiceV2ViewSet which imports from unpod/apiV2Platform/utils.py
    # This is separate from API v1 which calls external microservices

    # Task Runs - MongoDB direct (via apiV2Platform/utils.py)
    path(
        'spaces/<str:space_token>/runs/',
        TaskServiceV2ViewSet.as_view({"get": "get_space_runs"}),
        name='get_space_runs'
    ),
    path(
        'spaces/<str:space_token>/runs/<str:run_id>/tasks/',
        TaskServiceV2ViewSet.as_view({"get": "get_run_tasks"}),
        name='get_run_tasks'
    ),

    # Tasks - MongoDB direct (via apiV2Platform/utils.py)
    path(
        'spaces/<str:space_token>/tasks/',
        TaskServiceV2ViewSet.as_view({"post": "create_space_task", "get": "get_tasks_by_space_token"}),
        name='manage_space_task'
    ),
    path(
        'agents/',
        TaskServiceV2ViewSet.as_view({"get": "list_agents"}),
        name='list_agents_v2'
    ),
    path(
        'agents/<str:agent_handle>/tasks/',
        TaskServiceV2ViewSet.as_view({"get": "get_tasks_by_agent"}),
        name='Tasks by Agent ID V2'
    ),

    # Telephony Providers
    path(
        'telephony/providers/',
        TelephonyProvidersViewSet.as_view({"get": "get_providers"}),
        name='telephony_providers'
    ),

    # Provider Configurations
    path(
        'telephony/provider-configurations/',
        ProviderConfigurationsViewSet.as_view({"get": "get_provider_configurations", "post": "create_configuration"}),
        name='provider_configurations'
    ),
    path(
        'telephony/provider-configurations/<int:pk>/',
        ProviderConfigurationsViewSet.as_view({"get": "get_configuration", "patch": "update_configuration", "delete": "delete_configuration"}),
        name='provider_configuration_detail'
    ),

    # Telephony Numbers
    path(
        'telephony/numbers/',
        TelephonyNumbersViewSet.as_view({"get": "get_numbers"}),
        name='telephony_numbers'
    ),

    # Voice Bridges
    path(
        'telephony/bridges/',
        TelephonyBridgesViewSet.as_view({"get": "list_voice_bridges", "post": "create_voice_bridge"}),
        name='telephony_bridges'
    ),
    path(
        'telephony/bridges/<str:slug>/',
        TelephonyBridgesViewSet.as_view({"get": "get_voice_bridge", "patch": "update_voice_bridge", "delete": "delete_voice_bridge"}),
        name='telephony_bridge_detail'
    ),
    path(
        'telephony/bridges/<str:slug>/connect-provider/',
        TelephonyBridgesViewSet.as_view({"post": "connect_provider"}),
        name='telephony_bridge_connect_provider'
    ),
    path(
        'telephony/bridges/<str:slug>/disconnect-provider/',
        TelephonyBridgesViewSet.as_view({"post": "disconnect_provider"}),
        name='telephony_bridge_disconnect_provider'
    ),

    # Call Logs - MySQL direct (via apiV2Platform/utils.py)
    path('call-logs/', CallLogsViewSet.as_view({"get": "get_call_logs"}), name='get_call_logs'),

    # Spaces - Lightweight API for external users
    path('spaces/', SpaceV2ViewSet.as_view({"get": "list"}), name='space_list_v2'),
    path('spaces/<str:space_token>/', SpaceV2ViewSet.as_view({"get": "retrieve"}), name='space_detail_v2'),

    # Organizations - List user's org-handles
    path('organizations/', SpaceV2ViewSet.as_view({"get": "list_organizations"}), name='organization_list_v2'),

    # Reusing existing app URLs (commented out for now)
    # Uncomment when ready to add more endpoints
    # path('', include('unpod.users.urls'), name="users_v2_platform"),
    # path('', include('unpod.core_components.urls'), name="core_components_v2_platform"),
    # path('organization/', include('unpod.space.org_urls'), name="space_organization_v2_platform"),
    # path('spaces/', include('unpod.space.urls'), name="space_v2_platform"),
    # path('threads/', include('unpod.thread.urls'), name="thread_v2_platform"),
    # path('roles/', include('unpod.roles.urls'), name="roles_v2_platform"),
    # path('notifications/', include('unpod.notification.urls'), name="notification_v2_platform"),
    # path('subscriptions/', include('unpod.subscription.urls'), name="subscription_v2_platform"),
    # path('knowledge_base/', include('unpod.knowledge_base.urls'), name="knowledge_base_v2_platform"),
    # path('wallet/', include('unpod.wallet.urls'), name="wallet_v2_platform"),
    # path('channels/', include('unpod.channels.urls'), name="channels_v2_platform"),
    # path('telephony/', include('unpod.telephony.urls'), name="sip_v2_platform"),
    # path('documents/', include('unpod.documents.urls'), name="documents_v2_platform"),
    # path('contacts/', include('unpod.contacts.urls'), name="contacts_v2_platform"),
    # path('metrics/', include('unpod.metrics.urls'), name="metrics_v2_platform"),
    # path('dynamic-forms/', include('unpod.dynamic_forms.urls'), name="dynamic_forms_v2_platform"),
]
