from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import Sum

from unpod.common.enum import (
    TrunkDirection,
    TrunkType,
    TrunkStatus,
    GenericStatus,
    ConfigType,
    GenericDocumentsStatus,
    Regions,
)
from unpod.common.query import get_model_unique_code, generateSpaceSlug
from unpod.core_components.models import Provider, TelephonyNumber
from unpod.space.models import SpaceOrganization


class ProviderCredential(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    organization = models.ForeignKey(
        SpaceOrganization, on_delete=models.CASCADE, null=True, blank=True
    )
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    api_key = models.CharField(max_length=255, blank=True, null=True)
    api_secret = models.CharField(max_length=255, blank=True, null=True)
    base_url = models.CharField(max_length=255, blank=True, null=True)
    sip_url = models.CharField(max_length=255, blank=True, null=True)
    meta_json = models.JSONField(
        default=dict, encoder=DjangoJSONEncoder, blank=True, null=True
    )
    active = models.BooleanField(default=True)
    is_valid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.id} - {self.name} - {self.provider.name}"


class VoiceBridge(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=50, choices=GenericStatus.choices(), default=GenericStatus.DRAFT.name
    )
    numbers = models.ManyToManyField(TelephonyNumber, through="VoiceBridgeNumber")
    slug = models.CharField(max_length=50, db_index=True, blank=True, null=True)
    token = models.CharField(max_length=100, unique=True, blank=True, null=True)
    organization = models.ForeignKey(
        SpaceOrganization, on_delete=models.CASCADE, null=True, blank=True,
    )
    product_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    region = models.CharField(
        max_length=50, choices=Regions.choices(), default=Regions.IN.name
    )
    documents_status = models.CharField(
        max_length=50,
        choices=GenericDocumentsStatus.choices(),
        default=GenericDocumentsStatus.pending.name,
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        indexes = [
            # Composite index for common list query pattern (organization + product_id filtering)
            models.Index(fields=['organization', 'product_id'], name='vb_organization_product_idx'),
            # Slug lookup is already indexed via db_index=True
        ]

    def save(self, *args, **kwargs) -> None:
        if not self.token:
            self.token = get_model_unique_code(self.__class__, "token", N=24)
        if not self.slug:
            self.slug = generateSpaceSlug(self)
        return super().save(*args, **kwargs)

    @property
    def total_channels_count(self):
        """
        Calculate the total channels count by summing up channels_count from all related VoiceBridgeNumber records.
        This is calculated on the fly rather than stored in the database.
        """
        return (
            self.voicebridgenumber_set.aggregate(total=Sum("channels_count"))["total"]
            or 0
        )

    def __str__(self):
        return self.name


class VoiceBridgeNumber(models.Model):
    number = models.ForeignKey(
        TelephonyNumber, on_delete=models.CASCADE, null=True, blank=True
    )
    bridge = models.ForeignKey(VoiceBridge, on_delete=models.CASCADE)
    provider_credential = models.ForeignKey(
        ProviderCredential, on_delete=models.SET_NULL, null=True, blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=GenericStatus.choices(),
        default=GenericStatus.ACTIVE.name,
    )
    config_json = models.JSONField(
        default=dict, encoder=DjangoJSONEncoder, blank=True, null=True
    )
    channels_count = models.IntegerField(blank=True, default=1, null=True)
    connectivity_type = models.CharField(max_length=100, blank=True, null=True)
    agent_id = models.CharField(max_length=100, blank=True, null=True)
    has_trunks = models.BooleanField(default=False)
    sbc_config = models.JSONField(default=dict, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        unique_together = ("number", "bridge")
        ordering = ["-id"]
        indexes = [
            # Bridge and status lookup index (frequently filtered together)
            models.Index(fields=["bridge", "status"], name="vbn_bridge_status_idx"),
            # Provider credential lookup index
            models.Index(fields=["provider_credential"], name="vbn_provider_idx"),
            # Number lookup index
            models.Index(fields=["number"], name="vbn_number_idx"),
        ]

    def __str__(self):
        return f"{self.number.number if self.number else 'None'} - {self.bridge.name}"


class BridgeProviderConfig(models.Model):
    bridge = models.ForeignKey(VoiceBridge, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True, null=True)
    gateway_enabled = models.BooleanField(default=False)
    provider_credential = models.ForeignKey(
        ProviderCredential, on_delete=models.CASCADE, blank=True, null=True
    )
    service_type = models.CharField(
        max_length=20, choices=ConfigType.choices(), default=ConfigType.service
    )
    direction = models.CharField(
        max_length=20, blank=True, choices=TrunkDirection.choices()
    )
    trunk_type = models.CharField(max_length=20, choices=TrunkType.choices())
    address = models.CharField(max_length=255, blank=True, null=True)
    sip_refer = models.CharField(max_length=255, blank=True, null=True)
    sip_credentials_id = models.CharField(max_length=255, blank=True, null=True)
    headers_type = models.CharField(max_length=100, blank=True, null=True)
    username = models.CharField(max_length=50, blank=True, null=True)
    password = models.CharField(max_length=50, blank=True, null=True)
    numbers = models.JSONField(
        default=dict, encoder=DjangoJSONEncoder, blank=True, null=True
    )
    vbn_ids = models.JSONField(
        default=dict, encoder=DjangoJSONEncoder, blank=True, null=True
    )
    media_encryption = models.CharField(
        max_length=100, blank=True, null=True, default="disabled"
    )
    config = models.JSONField(
        default=dict, encoder=DjangoJSONEncoder, blank=True, null=True
    )
    status = models.CharField(
        max_length=20, choices=TrunkStatus.choices(), default=TrunkStatus.ACTIVE
    )
    error = models.TextField(blank=True, null=True)
    error_type = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.direction} - {self.numbers}"
