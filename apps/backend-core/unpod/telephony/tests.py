from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import TelephonyData, VoiceInfraProvider, VoiceBridge
from django.contrib.auth.models import User

class VoiceInfraViewSetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.provider_data = {
            "name": "Vapi",
            "api_key": "dummy_key",
            "secret": "dummy_secret",
            "sip_uri": "sip.vapi.ai"
        }

        self.bridge_data = {
            "org_id": "org_123",
            "name": "Test Bridge"
        }

    def test_create_provider(self):
        url = reverse("voiceinfra-viewset-create-provider")
        response = self.client.post(url, self.provider_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("provider_id", response.data)

    def test_create_bridge(self):
        url = reverse("voiceinfra-viewset-create-bridge")
        response = self.client.post(url, self.bridge_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("bridge_id", response.data)

    def test_associate_numbers(self):
        bridge = VoiceBridge.objects.create(**self.bridge_data)
        telephony = TelephonyData.objects.create(
            provider="Twilio",
            number="+1234567890",
            country="US",
            type="mobile",
            status="active"
        )
        url = reverse("voiceinfra-viewset-associate-numbers")
        response = self.client.post(url, {
            "bridge_id": bridge.id,
            "telephony_ids": [telephony.id]
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["success"], True)

    def test_create_trunk(self):
        bridge = VoiceBridge.objects.create(**self.bridge_data)
        provider = VoiceInfraProvider.objects.create(**self.provider_data)
        trunk_data = {
            "bridge_id": bridge.id,
            "provider_id": provider.id,
            "type": "voice_infra",
            "direction": "inbound",
            "config": {"example": "data"},
            "sip_refer_info": {"refer": True}
        }
        url = reverse("voiceinfra-viewset-create-trunk")
        response = self.client.post(url, trunk_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("trunk_id", response.data)

    def test_create_sip_trunk_missing_id(self):
        url = reverse("voiceinfra-viewset-create-sip-trunk")
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Note: A full integration test for `create_sip_trunk` with actual VAPI API would require mocking requests
