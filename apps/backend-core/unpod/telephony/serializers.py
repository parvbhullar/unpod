from rest_framework import serializers
from .models import (
    ProviderCredential,
    VoiceBridge,
    VoiceBridgeNumber,
    BridgeProviderConfig,
)
from ..core_components.serializers import ProviderSerializer
# from ..common.storage_backends import imagekitBackend
from ..space.models import SpaceOrganization
from ..space.serializers import SpaceOrganizationSerializers


# class ProviderSerializer(serializers.ModelSerializer):
#     icon = serializers.SerializerMethodField()
#     form_slug = serializers.CharField(source="form.slug", read_only=True)
#
#     class Meta:
#         model = Provider
#         fields = [
#             "id",
#             "name",
#             "type",
#             # "model_type",
#             "model_types",
#             "url",
#             "description",
#             "icon",
#             "form_slug",
#             "status",
#         ]
#
#     def get_icon(self, obj):
#         if obj.icon:
#             return imagekitBackend.generateURL(obj.icon.name)
#         return None


class ProviderCredentialSerializer(serializers.ModelSerializer):
    provider_details = ProviderSerializer(source="provider", read_only=True)
    organization = serializers.PrimaryKeyRelatedField(
        queryset=SpaceOrganization.objects.all(), required=False
    )

    class Meta:
        model = ProviderCredential
        fields = [
            "id",
            "name",
            "provider",
            "provider_details",
            "organization",
            "meta_json",
            "active",
            "api_key",
            "api_secret",
            "base_url",
            "sip_url",
            "is_valid",
        ]


# class TelephonyNumberSerializer(serializers.ModelSerializer):
#     provider = serializers.PrimaryKeyRelatedField(
#         queryset=Provider.objects.all(), write_only=True
#     )
#     provider_details = ProviderSerializer(source="provider", read_only=True)
#
#     class Meta:
#         model = TelephonyNumber
#         fields = [
#             "id",
#             "number",
#             "provider",
#             "provider_details",
#             "country_code",
#             "region",
#             "state",
#             "active",
#             "owner_type",
#             "number_type",
#             "association",
#             "agent_number",
#         ]


class VoiceBridgeSerializer(serializers.ModelSerializer):
    organization_details = SpaceOrganizationSerializers(source="organization", read_only=True)

    numberIds = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )

    numbers = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = VoiceBridge
        fields = [
            "id",
            "name",
            "description",
            "status",
            "documents_status",
            "numberIds",
            "slug",
            "numbers",
            "organization",
            "region",
            "organization_details",
        ]

    def get_numbers(self, obj):
        # from .serializers import TelephonyNumberSerializer  # or import at top
        bridge_numbers = VoiceBridgeNumber.objects.filter(
            bridge=obj, number__isnull=False
        ).select_related("number__provider")
        return VoiceBridgeNumberWithDetailsSerializer(bridge_numbers, many=True).data

    # def to_representation(self, instance):
    #     rep = super().to_representation(instance)
    #     if isinstance(instance.status, Enum):
    #         rep['status'] = instance.status.value
    #     return rep

    def create(self, validated_data):
        print("Creating VoiceBridge with validated_data:", validated_data)
        number_ids = validated_data.pop("numberIds", [])
        bridge = VoiceBridge.objects.create(**validated_data)
        for number_id in number_ids:
            VoiceBridgeNumber.objects.create(
                bridge=bridge, number_id=number_id, status="active"
            )
        return bridge

    def update(self, instance, validated_data):
        print("Updating VoiceBridge with validated_data:", validated_data)
        number_ids = validated_data.pop("numberIds", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # if number_ids is not None:
        #     existing_numbers = set(
        #         VoiceBridgeNumber.objects.filter(bridge=instance).values_list("number_id", flat=True)
        #     )
        #     new_number_ids = set(number_ids) - existing_numbers
        #     remove_number_ids = existing_numbers - set(number_ids)
        #
        #     VoiceBridgeNumber.objects.filter(bridge=instance, number_id__in=remove_number_ids).delete()
        #     numbers_to_add = TelephonyNumber.objects.filter(id__in=new_number_ids)
        #     for number in numbers_to_add:
        #         VoiceBridgeNumber.objects.create(bridge=instance, number=number, status='active')

        return instance


# class VoiceBridgeNumberNestedSerializer(serializers.ModelSerializer):
#     number = TelephonyNumberSerializer(read_only=True)
#     provider_credential = ProviderCredentialSerializer(read_only=True)
#
#     class Meta:
#         model = VoiceBridgeNumber
#         fields = [
#             "id", "number", "provider_credential",
#             "status", "connectivity_type", "agent", "config_json"
#         ]


class VoiceBridgeNumberWithDetailsSerializer(serializers.ModelSerializer):
    number_id = serializers.IntegerField(source="number.id")
    number = serializers.CharField(source="number.number")
    state = serializers.CharField(source="number.state")
    active = serializers.BooleanField(source="number.active")
    provider_details = ProviderSerializer(source="number.provider", read_only=True)
    provider_credential = ProviderCredentialSerializer(read_only=True)

    class Meta:
        model = VoiceBridgeNumber
        fields = [
            "id",
            "number_id",
            "number",
            "state",
            "active",
            "channels_count",
            "provider_details",
            "provider_credential",
            "status",
            "connectivity_type",
            "agent_id",
            "config_json",
        ]


class VoiceBridgeNumberSerializer(serializers.ModelSerializer):
    provider_credential = ProviderCredentialSerializer(read_only=True)
    provider_credential_id = serializers.PrimaryKeyRelatedField(
        queryset=ProviderCredential.objects.all(),
        source="provider_credential",
        write_only=True,
        required=False,
    )

    class Meta:
        model = VoiceBridgeNumber
        fields = [
            "id",
            "number",
            "number_id",
            "bridge",
            "bridge_id",
            "channels_count",
            "provider_credential",
            "provider_credential_id",
            "status",
            "connectivity_type",
            "agent_id",
            "config_json",
        ]

    # def to_representation(self, instance):
    #     rep = super().to_representation(instance)
    #     if isinstance(instance.status, Enum):
    #         rep["status"] = instance.status.value.name
    #     return rep

    # def validate(self, data):
    #     # prevent duplicate VoiceBridgeNumber
    #     number = data.get("number") or self.instance.number if self.instance else None
    #     bridge = data.get("bridge") or self.instance.bridge if self.instance else None
    #     if number and bridge:
    #         existing = VoiceBridgeNumber.objects.filter(number=number, bridge=bridge)
    #         if self.instance:
    #             existing = existing.exclude(pk=self.instance.pk)
    #         if existing.exists():
    #             raise serializers.ValidationError("This number is already associated with this bridge.")
    #     return data


class TrunkSerializer(serializers.ModelSerializer):
    bridge_slug = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    provider = serializers.SerializerMethodField()

    class Meta:
        model = BridgeProviderConfig
        fields = [
            "id",
            "name",
            "bridge_slug",
            "provider",
            "provider_credential",
            "service_type",
            "direction",
            "trunk_type",
            "address",
            "sip_refer",
            "headers_type",
            "numbers",
            "media_encryption",
            "config",
            "status",
        ]

    @staticmethod
    def get_status(obj):
        if isinstance(obj.status, str) and "." in obj.status:
            # Extract after the dot (e.g., "TrunkStatus.ACTIVE" → "ACTIVE")
            return obj.status.split(".")[-1].lower()
        return obj.status.lower() if isinstance(obj.status, str) else obj.status

    @staticmethod
    def get_bridge_slug(obj):
        return obj.bridge.slug if obj.bridge else None

    @staticmethod
    def get_provider(obj):
        try:
            return obj.provider_credential.provider.name
        except AttributeError:
            return None


class TrunkDetailSerializer(serializers.ModelSerializer):
    bridge_slug = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    provider = serializers.SerializerMethodField()

    class Meta:
        model = BridgeProviderConfig
        fields = "__all__"  # Or specify detailed fields

    @staticmethod
    def get_status(obj):
        if isinstance(obj.status, str) and "." in obj.status:
            # Extract after the dot (e.g., "TrunkStatus.ACTIVE" → "ACTIVE")
            return obj.status.split(".")[-1].lower()
        return obj.status.lower() if isinstance(obj.status, str) else obj.status

    @staticmethod
    def get_bridge_slug(obj):
        return obj.bridge.slug if obj.bridge else None

    @staticmethod
    def get_provider(obj):
        try:
            return obj.provider_credential.provider.name
        except AttributeError:
            return None
