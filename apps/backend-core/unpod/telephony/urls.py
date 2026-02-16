# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ProviderCredentialViewSet,
    TelephonyNumberViewSet,
    VoiceBridgeViewSet,
    TrunkViewSet,
    CreateTrunkViewSet,
    VoiceBridgeNumberViewSet,
    update_document_status,
)

router = DefaultRouter()
router.register(
    r"provider-credentials", ProviderCredentialViewSet, basename="provider-credential"
)
router.register(r"bridges", VoiceBridgeViewSet, basename="bridge")
router.register(r"bridge-numbers", VoiceBridgeNumberViewSet, basename="bridge-number")
router.register(r"trunks", TrunkViewSet, basename="trunk")
router.register(r"vapi/trunks", CreateTrunkViewSet, basename="vapi-trunk")

urlpatterns = [
    path("", include(router.urls)),
    # Telephony Numbers
    path(
        "numbers/",
        TelephonyNumberViewSet.as_view({"post": "create"}),
        name="numbers"
    ),
    path(
        "numbers/<int:number_id>/unlink-provider/",
        TelephonyNumberViewSet.as_view({"post": "unlink_provider"}),
        name="unlink_provider"
    ),
    path(
        "admin/telephony/voicebridge/<int:bridge_id>/update-document-status/<int:doc_id>/<str:doc_status>",
        update_document_status,
        name="update_document_status",
    ),
]
