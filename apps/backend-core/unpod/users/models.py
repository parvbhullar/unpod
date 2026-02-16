from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils.translation import gettext_lazy as _

from unpod.common.mixin import CreatedUpdatedMixin
from model_utils.models import TimeStampedModel
from unpod.common.storage_backends import PrivateMediaStorage
from unpod.common.string import generate_code, generate_color_hex, split_full_name
from unpod.common.validation import fetch_email_domain, validate_email_type


def get_unique_code(N=16):
    token = generate_code(N)
    while User.objects.filter(user_token=token).exists():
        token = generate_code(N)
    return token


def get_referrer_code():
    token = generate_code(6)
    while User.objects.filter(referrer_code=token).exists():
        token = generate_code(6)
    return token


class User(AbstractUser, CreatedUpdatedMixin):
    """Default user for Freedom."""

    phone_number = models.CharField(
        "Mobile Number", max_length=20, blank=True, null=True
    )
    verify_mob = models.BooleanField("Verify Mobile Number", default=False)
    verify_email = models.BooleanField("Verify Email", default=False)
    is_social = models.BooleanField("Social Sign in", default=False)
    user_token = models.CharField("User Token", max_length=20, blank=True, null=True)
    referrer_code = models.CharField(
        "Referrer Code", max_length=20, blank=True, null=True
    )
    activity = GenericRelation("core_components.PilotLink", related_query_name="users")

    CHOICES = (("Mobile", "Mobile"), ("Email", "Email"), ("Social", "Social"))
    mode = models.CharField(
        "Mode", max_length=20, choices=CHOICES, default="Mobile", null=True, blank=True
    )

    def get_username(self):
        return self.username

    @property
    def full_name(self):
        name = ""
        if self.first_name:
            name = name + self.first_name + " "
        if self.last_name:
            name = name + self.last_name
        return name

    def save(self, *args, **kwargs) -> None:
        if not self.user_token:
            self.user_token = get_unique_code()
        if not self.referrer_code:
            self.referrer_code = get_referrer_code()
        return super().save(*args, **kwargs)

    def update_name(self, name):
        name = name.strip()
        first_name, last_name = split_full_name(name)
        update_data = {}
        if first_name != "":
            update_data.update({"first_name": first_name})
        if last_name != "":
            update_data.update({"last_name": last_name})
        if len(update_data):
            self = self.updateModel(update_data)
        return self

    @property
    def organization(self):
        if hasattr(self, "userbasicdetail_user"):
            if self.userbasicdetail_user.active_organization:
                return self.userbasicdetail_user.active_organization
        from unpod.space.models import SpaceOrganization
        from unpod.users.utils import updateActiveOrg

        unique_org = (
            self.organizationmemberroles_user.all()
            .values_list("organization_id", flat=True)
            .distinct()
        )
        if len(unique_org):
            org_list = SpaceOrganization.objects.filter(id__in=unique_org)
            if org_list.count() > 1:
                if validate_email_type(self.email):
                    domain = fetch_email_domain(self.email)
                    org_list = org_list.filter(
                        is_private_domain=True, domain_handle=domain
                    )
                    if org_list:
                        updateActiveOrg(self, org_list[0])
                        return org_list[0]
                updateActiveOrg(self, org_list[0])
                return org_list[0]
            if org_list:
                updateActiveOrg(self, org_list[0])
                return org_list[0]
        return None


class UserInviteToken(CreatedUpdatedMixin):
    invited_by_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_invited_by_user",
    )
    invite_token = models.CharField("User Token", max_length=30, blank=True, null=True)
    user_email = models.EmailField(_("email address"), blank=True)
    valid_time = models.DateTimeField(null=True, blank=True)
    success = models.BooleanField(default=False)
    verify = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = "User Invite Token"
        verbose_name_plural = "User Invite Token"


class Roles(TimeStampedModel):
    name = models.CharField(max_length=99)
    code = models.CharField(max_length=99, blank=True, null=True, db_index=True)
    role_type = models.CharField(max_length=20)

    def __str__(self) -> str:
        return self.name


class UserRoles(TimeStampedModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="%(class)s_user",
    )
    role = models.ForeignKey(
        Roles,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_role",
    )


class UserBasicDetail(CreatedUpdatedMixin):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="%(class)s_user",
    )
    role_name = models.CharField(max_length=99, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    profile_color = models.CharField(blank=True, null=True, max_length=20)
    profile_picture = models.FileField(
        upload_to="private/profile",
        null=True,
        blank=True,
        storage=PrivateMediaStorage(file_overwrite=True),
    )
    active_organization = models.ForeignKey(
        "space.SpaceOrganization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_active_organization",
    )
    active_space = models.ForeignKey(
        "space.Space",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_active_space",
    )

    def save(self, *args, **kwargs):
        if self.profile_color is None:
            self.profile_color = generate_color_hex()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user}"


class BlackListToken(TimeStampedModel):
    token = models.TextField("Token", null=True, blank=True)
    user_id = models.IntegerField(null=True, blank=True)


class UserDevice(models.Model):
    """
    Stores details about each user's mobile device and FCM token.
    Used for push notifications, tracking, and session management.
    """

    DEVICE_TYPE_CHOICES = [
        ("android", "Android"),
        ("ios", "iOS"),
        ("web", "Web"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="devices",
        null=True,
        blank=True,
        help_text="User associated with this device (optional for anonymous tokens)",
    )
    device_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="Unique device identifier (UUID, IMEI, or vendor ID)",
    )
    is_active = models.BooleanField(
        default=True, help_text="Disable to stop sending push notifications"
    )
    fcm_token = models.TextField(
        help_text="Firebase Cloud Messaging registration token"
    )
    device_type = models.CharField(
        max_length=20,
        choices=DEVICE_TYPE_CHOICES,
        default="android",
    )
    device_model = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Model of the device (e.g. iPhone 14, Samsung Galaxy S23)",
    )
    language = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Device language setting (e.g. en-US, fr-FR)",
    )
    timezone = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Device timezone (e.g. America/New_York)",
    )
    ip_address = models.GenericIPAddressField(
        blank=True, null=True, help_text="Last known IP address of the device"
    )
    location = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Last known location of the device (if available)",
    )
    app_version = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="App version installed on the device",
    )
    os_version = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Operating system version (e.g. Android 14, iOS 18)",
    )
    last_login = models.DateTimeField(
        auto_now=True, help_text="Last time this device was used to log in"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Device"
        verbose_name_plural = "User Devices"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.user} - {self.device_type} ({self.device_id})"
