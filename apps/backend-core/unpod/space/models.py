from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.conf import settings
from unpod.common.enum import (
    OrgTypes,
    PrivacyType,
    SpaceType,
    KnowledgeBaseContentType,
    StatusType,
    Regions,
)

from unpod.common.mixin import CreatedUpdatedMixin
from unpod.common.query import get_model_unique_code, generateSpaceSlug
from unpod.common.storage_backends import PrivateMediaStorage
from unpod.roles.models import AccountTags, Roles


# fmt: off
class SpaceOrganization(CreatedUpdatedMixin):
    name = models.CharField(max_length=99, db_index=True)
    token = models.CharField(max_length=30, blank=True, null=True, db_index=True)
    domain = models.CharField(max_length=99, blank=True, null=True)
    domain_handle = models.CharField(max_length=99, blank=True, null=True)
    is_private_domain = models.BooleanField(default=False)
    account_type = models.ForeignKey(AccountTags, on_delete=models.SET_NULL, related_name='%(class)s_account_type',
                                     null=True, blank=True)
    privacy_type = models.CharField(choices=PrivacyType.choices(), default=PrivacyType.public.name, max_length=20)
    color = models.CharField(max_length=20, blank=True, null=True)
    logo = models.FileField(upload_to='private/organization', null=True, blank=True,
                            storage=PrivateMediaStorage(file_overwrite=True))
    description = models.TextField(blank=True, null=True)
    seeking = models.ManyToManyField(AccountTags, related_name='%(class)s_seeking', blank=True)
    tags = models.ManyToManyField(AccountTags, related_name='%(class)s_tags', blank=True)
    pilots = GenericRelation('core_components.PilotLink', related_query_name='organizations')
    org_type = models.CharField(choices=OrgTypes.choices(), default=OrgTypes.free.name, max_length=20, db_index=True)
    status = models.CharField(max_length=20, choices=StatusType.choices(), default=StatusType.active.name,
                              db_index=True)
    region = models.CharField(
        max_length=50, choices=Regions.choices(), default=Regions.IN.name
    )
    pilot = models.ForeignKey(
        'core_components.Pilot',
        on_delete=models.SET_NULL,
        related_name='%(class)s_pilot',
        null=True,
        blank=True
    )
    telephony_number = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        indexes = [
            # Domain handle lookup index (frequently queried for tenant resolution)
            models.Index(fields=['domain_handle'], name='org_domain_idx'),
            # Active organizations index (filtering by status and creation date)
            models.Index(fields=['status', 'created'], name='org_active_idx'),
        ]

    def save(self, *args, **kwargs) -> None:
        if not self.token:
            self.token = get_model_unique_code(self.__class__, 'token', N=20)
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.name} - {self.token}"


class OrganizationMemberRoles(CreatedUpdatedMixin):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='%(class)s_user',
                             null=True, blank=True)
    organization = models.ForeignKey(SpaceOrganization, on_delete=models.SET_NULL,
                                     related_name='%(class)s_organization', null=True, blank=True)
    role = models.ForeignKey(Roles, on_delete=models.SET_NULL, related_name='%(class)s_role', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    grant_by = models.IntegerField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.user} - {self.organization} - {self.role}"


class Space(CreatedUpdatedMixin):
    space_organization = models.ForeignKey(SpaceOrganization, on_delete=models.SET_NULL,
                                           related_name='%(class)s_space_organization', null=True, blank=True)
    name = models.CharField(max_length=99, db_index=True)
    token = models.CharField(max_length=30, blank=True, null=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    privacy_type = models.CharField(choices=PrivacyType.choices(), default=PrivacyType.public.name, max_length=20)
    slug = models.CharField(db_index=True, max_length=199, blank=True, null=True)
    logo = models.FileField(upload_to='private/space', null=True, blank=True,
                            storage=PrivateMediaStorage(file_overwrite=True))
    is_default = models.BooleanField(default=False)
    space_type = models.CharField(choices=SpaceType.choices(), default=SpaceType.general.name, max_length=20)
    content_type = models.CharField(choices=KnowledgeBaseContentType.choices(),
                                    default=KnowledgeBaseContentType.general.name, max_length=20)
    pilots = GenericRelation('core_components.PilotLink', related_query_name='spaces')
    app_configs = GenericRelation('channels.AppConfigLink', related_query_name='spaces')
    status = models.CharField(max_length=20, choices=StatusType.choices(), default=StatusType.active.name,
                              db_index=True)

    class Meta:
        indexes = [
            # Organization and space type lookup index (commonly filtered together)
            models.Index(fields=['space_organization', 'space_type'], name='space_org_type_idx'),
        ]

    def save(self, *args, **kwargs) -> None:
        if not self.token:
            self.token = get_model_unique_code(self.__class__, 'token', N=24)
        if not self.slug:
            self.slug = generateSpaceSlug(self)
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.name} - {self.token}"


class SpaceMemberRoles(CreatedUpdatedMixin):
    role = models.ForeignKey(Roles, on_delete=models.SET_NULL,
                             related_name='%(class)s_role', null=True, blank=True)
    space = models.ForeignKey(Space, on_delete=models.CASCADE, related_name='%(class)s_space', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='%(class)s_user', null=True, blank=True)
    grant_by = models.IntegerField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.user} - {self.space} - {self.role}"


class SpaceInvite(CreatedUpdatedMixin):
    space = models.ForeignKey(Space, on_delete=models.CASCADE, related_name='%(class)s_space', null=True, blank=True)
    role = models.ForeignKey(Roles, on_delete=models.SET_NULL,
                             related_name='%(class)s_role', null=True, blank=True)
    invite_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                  related_name='%(class)s_invite_by', null=True, blank=True)
    invite_token = models.CharField(max_length=40, blank=True, null=True)
    valid_upto = models.DateTimeField(null=True, blank=True)
    valid_from = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    user_email = models.EmailField(blank=True, null=True)
    invite_verified = models.BooleanField(default=False)
    invite_verify_dt = models.DateTimeField(blank=True, null=True)
    is_joined = models.BooleanField(default=False)
    joined_dt = models.DateTimeField(blank=True, null=True)
    expired = models.BooleanField(default=False)
    expired_dt = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs) -> None:
        if not self.invite_token:
            self.invite_token = get_model_unique_code(self.__class__, 'invite_token', N=20)
        return super().save(*args, **kwargs)


class SpaceAccessRequest(CreatedUpdatedMixin):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='%(class)s_user',
                             null=True, blank=True)
    space = models.ForeignKey(Space, on_delete=models.CASCADE, related_name='%(class)s_space', null=True, blank=True)
    role = models.ForeignKey(Roles, on_delete=models.SET_NULL, related_name='%(class)s_role', null=True, blank=True)
    request_token = models.CharField(max_length=40, blank=True, null=True, db_index=True)
    request_type = models.CharField(
        max_length=20,
        choices=[('access_request', 'Access Request'), ('change_role', 'Change Role')],
        default='access_request'
    )
    valid_from = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    request_verified = models.BooleanField(default=False)
    request_verify_dt = models.DateTimeField(blank=True, null=True)
    is_joined = models.BooleanField(default=False)
    joined_dt = models.DateTimeField(blank=True, null=True)
    is_expired = models.BooleanField(default=False)

    def save(self, *args, **kwargs) -> None:
        if not self.request_token:
            self.request_token = get_model_unique_code(self.__class__, 'request_token', N=16)
        return super().save(*args, **kwargs)


class OrganizationInvite(CreatedUpdatedMixin):
    organization = models.ForeignKey(SpaceOrganization, on_delete=models.CASCADE, related_name='%(class)s_organization',
                                     null=True, blank=True)
    role = models.ForeignKey(Roles, on_delete=models.SET_NULL,
                             related_name='%(class)s_role', null=True, blank=True)
    invite_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                  related_name='%(class)s_invite_by', null=True, blank=True)
    invite_token = models.CharField(max_length=40, blank=True, null=True)
    valid_upto = models.DateTimeField(null=True, blank=True)
    valid_from = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    user_email = models.EmailField(blank=True, null=True)
    invite_verified = models.BooleanField(default=False)
    invite_verify_dt = models.DateTimeField(blank=True, null=True)
    is_joined = models.BooleanField(default=False)
    joined_dt = models.DateTimeField(blank=True, null=True)
    expired = models.BooleanField(default=False)
    expired_dt = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs) -> None:
        if not self.invite_token:
            self.invite_token = get_model_unique_code(self.__class__, 'invite_token', N=20)
        return super().save(*args, **kwargs)


class OrganizationAccessRequest(CreatedUpdatedMixin):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='%(class)s_user',
                             null=True, blank=True)
    organization = models.ForeignKey(SpaceOrganization, on_delete=models.CASCADE, related_name='%(class)s_organization',
                                     null=True, blank=True)
    role = models.ForeignKey(Roles, on_delete=models.SET_NULL, related_name='%(class)s_role', null=True, blank=True)
    request_token = models.CharField(max_length=40, blank=True, null=True, db_index=True)
    request_type = models.CharField(
        max_length=20,
        choices=[('access_request', 'Access Request'), ('change_role', 'Change Role')],
        default='access_request'
    )
    valid_from = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    request_verified = models.BooleanField(default=False)
    request_verify_dt = models.DateTimeField(blank=True, null=True)
    is_joined = models.BooleanField(default=False)
    joined_dt = models.DateTimeField(blank=True, null=True)
    is_expired = models.BooleanField(default=False)

    def save(self, *args, **kwargs) -> None:
        if not self.request_token:
            self.request_token = get_model_unique_code(self.__class__, 'request_token', N=16)
        return super().save(*args, **kwargs)


class SpaceOrganizationBillingInfo(models.Model):
    """Stores billing details for a organization."""

    organization = models.ForeignKey(
        SpaceOrganization,
        on_delete=models.CASCADE,
        related_name="billing_infos",
        null=True,
        blank=True,
    )
    tax_ids = models.JSONField(default=list, blank=True,
                               null=True)  # Store structured tax IDs: [{"country": "IN", "type": "GST", "number": "09AAGCG5070P1Z1"}]
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default="India")
    postal_code = models.CharField(max_length=20)

    contact_person = models.CharField(max_length=150, blank=True, null=True)
    phone_number_cc = models.CharField(max_length=10, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)

    default = models.BooleanField(default=False, help_text="Mark this as default billing address.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Organization Billing Information"
        verbose_name_plural = "Organization Billing Information"
        ordering = ["-default", "-updated_at"]
