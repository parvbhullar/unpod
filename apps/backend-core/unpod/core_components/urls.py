from django.urls import path

from unpod.core_components.views import (
    ApiMediaResourceViewSet,
    GlobalInvitationViewSet,
    KnowledgebaseEvalsViewSet,
    MessagingServiceViewSet,
    BasicSettingViewSet,
    PilotViewSet,
    PluginViewSet,
    ModelViewSet,
    GenerateAIPersona,
    KBViewSet,
    TagViewSet,
    PilotPermissionViewSet,
    RelevantTagListView,
    RelevantTagLinkCreateView,
    RelevantTagLinkDeleteView,
    VoiceProfilesViewSet,
    VoicesViewSet,
    GlobalSystemConfigViewSet,
    ApiMediaPublicResourceViewSet,
    PilotTemplateViewSet,
    WebsiteInfoViewSet,
    UseCasesViewSet,
    PilotTestViewSet,
    TelephonyNumberViewSet,
    ProviderViewSet,
)
from unpod.core_components.voices.views import LiveKitVoiceViewSet

app_name = "core_components_v1"
# fmt: off
urlpatterns = [
    path('media/upload/',  ApiMediaResourceViewSet.as_view({"post": "upload"}), name='media-upload'),
    path('media/upload-multiple/',  ApiMediaResourceViewSet.as_view({"post": "upload_multiple"}), name='media-upload-multiple'),
    path('media/upload/get-upload-url/',  ApiMediaResourceViewSet.as_view({"post": "get_upload_url"}), name='media-get-upload'),
    path('media/pre-signed-url/',  ApiMediaResourceViewSet.as_view({"get": "pre_signed_url"}), name='media-pre-signed-url'),
    path('media/download-signed-url/',  ApiMediaPublicResourceViewSet.as_view({"get": "download_signed_url"}), name='media-download-signed-url'),
    path('media/<str:object_type>/<str:object_id>/', ApiMediaResourceViewSet.as_view({"get": "list"}), name='media'),
    path('media/<str:media_id>/',  ApiMediaResourceViewSet.as_view({"get": "get"}), name='media-get'),

    path('core/basic-settings/',  BasicSettingViewSet.as_view({"get": "basic_setting"}), name='get-basic_setting'),
    path('core/invite/subscribe/',  GlobalInvitationViewSet.as_view({"post": "invite_subscribe"}), name='core-invite-subscribe'),
    path('core/invite/verify/',  GlobalInvitationViewSet.as_view({"post": "inviteVerify"}), name='core-invite-verify'),
    path('core/sitemap/<str:sitemap_file>/',  BasicSettingViewSet.as_view({"get": "get_sitemap_file"}), name='get-sitemap-file'),
    path('conversation/<str:thread_id>/messages/',  MessagingServiceViewSet.as_view({"get": "postData"}), name='conversation-thread_id-messages'),

    path('core/website-info/', WebsiteInfoViewSet.as_view({"get": "website_info"}), name='website_info'),
    path('core/pilots/menus/', PilotViewSet.as_view({"get": "get_menus_list"}), name='get_menus_list'),
    path('core/pilots/<str:handle>/unlink-space/', PilotViewSet.as_view({"get": "unlink_space"}), name='unlink_space'),
    path('core/pilots/<str:handle>/clone/', PilotViewSet.as_view({"post": "clone_pilot"}), name='clone_pilot'),
    path('core/pilots/<str:handle>/export-details/', PilotViewSet.as_view({"get": "export_details"}), name='export_details'),
    path('core/pilots/check_handle/', PilotViewSet.as_view({"get": "check_handle_available"}), name='check_handle'),
    path('core/pilots/public/', MessagingServiceViewSet.as_view({"get": "public_pilots"}), name='public_pilots'),
    path('core/pilots/org/', PilotViewSet.as_view({"get": "org_pilot_list"}), name='pilots_org_list'),
    path('core/pilots/<str:handle>/', PilotViewSet.as_view({"get": "retrieve", "put": "update_pilot", "delete": "destroy"}), name='pilots'),
    path('core/pilots/<str:handle>/reaction/', PilotViewSet.as_view({"put": "update_reaction", "get": "reaction_info"}), name='pilot_reaction'),
    path('core/pilots/<str:handle>/permission/', PilotPermissionViewSet.as_view({"post": "post"}), name='pilot_permission_add'),
    path('core/pilots/permission/<str:handle>/', PilotPermissionViewSet.as_view({"put": "update"}), name='pilot_permission_update'),
    path('core/pilots/', PilotViewSet.as_view({"get": "list", "post": "create_pilot"}), name='pilots'),


    path('core/plugins/', PluginViewSet.as_view({"get": "list"}), name='plugin_list'),
    path('core/knowledgebase/', KBViewSet.as_view({"get": "list"}), name='kb_list'),
    path('core/models/', ModelViewSet.as_view({"get": "list"}), name='models_list'),
    path("core/providers/", ProviderViewSet.as_view({"get": "list"}), name="providers-list"),
    path("core/providers/models/", ProviderViewSet.as_view({"get": "get_model_providers"}), name="get_model_providers"),
    path('core/providers/models/<str:provider_id>/', ModelViewSet.as_view({"get": "provider_models_list"}), name='provider_models_list'),
    path('core/tags/', TagViewSet.as_view({"get": "list"}), name='tags_list'),
    path(
        'core/generate-ai-persona/',
        GenerateAIPersona.as_view({"get": "get", "post": "generate_ai_persona"}),
        name='generate_ai_persona'
    ),

    # tags
    path('core/relevant-tags/', RelevantTagListView.as_view({"get": "get"}), name='relevant-tags'),
    path('core/relevant-tags/create/', RelevantTagLinkCreateView.as_view({"post": "post"}), name='relevant-tags-link-create'),
    path('core/relevant-tags/update/', RelevantTagLinkCreateView.as_view({"put": "put"}), name='relevant-tags-link-update'),
    path('core/relevant-tags/delete/', RelevantTagLinkDeleteView.as_view({"delete": "delete"}), name='relevant-tags-link-delete'),
    path('core/relevant-tags/bulk-create/', RelevantTagLinkCreateView.as_view({"post": "bulk_create"}), name='relevant-tags-bulk-create'),


    # voice
    path("core/voice/<str:post_slug>/generate_room_token/", LiveKitVoiceViewSet.as_view({"get": "get_livekit_token"}), name="voice_room_token"),
    path("core/voice/generate_room_token/public_token/", LiveKitVoiceViewSet.as_view({"post": "room_livekit_token"}), name="room_livekit_token"),
    path("core/voice/delete_room/<str:room_name>/", LiveKitVoiceViewSet.as_view({"delete": "livekit_delete_room"}), name="livekit_delete_room"),

    #voice-profiles
    path("core/voice-profiles/", VoiceProfilesViewSet.as_view({"get": "get"}), name="voice-profiles"),
    path("core/voice-profiles/<str:profile_id>/", VoiceProfilesViewSet.as_view({"get": "fetch"}), name="voice-profiles-detail"),
    path("core/voice-profiles/create/", VoiceProfilesViewSet.as_view({"post": "post"}), name="voice-profiles-create"),
    path("core/voice-profiles/<str:profile_id>/", VoiceProfilesViewSet.as_view({"patch": "patch"}), name="voice-profiles-update"),

    # Voices
    path("core/voices/<str:provider>/<str:voice_id>/",VoicesViewSet.as_view({"get": "get_voice_media"}), name="get_voice_media"),
    path("core/voices/<str:profile_id>/",VoicesViewSet.as_view({"get": "get_profile_voice"}), name="get_profile_voice"),

    #system configs
    path("core/global-config/",GlobalSystemConfigViewSet.as_view({"get": "get"}), name="global-config-get"),
    path("core/global-config/", GlobalSystemConfigViewSet.as_view({"post": "post"}), name="global-config-create"),

    # Pilot Templates
    path("core/pilot-templates/", PilotTemplateViewSet.as_view({"get": "list"}), name="template-list"),

    path("core/knowledgebase-evals/generate/", KnowledgebaseEvalsViewSet.as_view({"post": "generate_evals"}), name="knowledgebase-evals-generate"),
    path("core/knowledgebase-evals/fetch-evals/", KnowledgebaseEvalsViewSet.as_view({"post": "fetch_evals"}), name="knowledgebase-evals-fetch-evals"),

    # Use Cases
    path("core/use-cases/", UseCasesViewSet.as_view({"get": "list"}), name="use-cases-list"),

    # Telephony Numbers
    path("core/telephony-numbers/", TelephonyNumberViewSet.as_view({"get": "list"}), name="telephony-numbers-list"),

    #agent_test
    path("core/tests/test-agent/", PilotTestViewSet.as_view({"post": "agent_eval_testing"}), name="test-agent-eval"),
    path("core/tests/test-agent/<str:agent_id>/",PilotTestViewSet.as_view({"get": "get_test_results"}), name="get_test_results"),
]
