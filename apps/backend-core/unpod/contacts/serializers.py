from rest_framework import serializers
from .models import Contact


class ContactSerializer(serializers.ModelSerializer):
    products = serializers.ListField(
        child=serializers.ChoiceField(
            choices=[
                "Sip Bridging",
                "Voice AI Infra",
                "Voice AI Agents",
                "Voice Models(STT, TTS)",
            ]
        )
    )

    class Meta:
        model = Contact
        fields = [
            "id",
            "name",
            "email",
            "business",
            "phone_cc",
            "phone",
            "alt_phone_cc",
            "alt_phone",
            "products",
            "status",
            "product_id",
        ]
