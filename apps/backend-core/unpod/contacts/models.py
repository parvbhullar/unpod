from django.conf import settings
from django.db import models
from django.utils import timezone


class Contact(models.Model):
    SOFTWARE_CHOICES = [
        ("Sip Bridging", "Sip Bridging"),
        ("Voice AI Infra", "Voice AI Infra"),
        ("Voice AI Agents", "Voice AI Agents"),
        ("Voice Models(STT, TTS)", "Voice Models(STT, TTS)"),
    ]
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    business = models.CharField(max_length=255)
    phone_cc = models.CharField(max_length=10, blank=True, null=True)
    phone = models.CharField(max_length=20)
    alt_phone_cc = models.CharField(max_length=10, blank=True, null=True)
    alt_phone = models.CharField(
        max_length=20, blank=True, null=True, help_text="Alternative phone number"
    )
    registered_as_user = models.BooleanField(
        help_text="If checked, the contact is saved as a user.", default=False
    )
    user_register_date = models.DateTimeField(
        null=True, blank=True, help_text="Date when the user was registered"
    )
    products = models.JSONField(
        default=list,
        help_text="List of products used. Options: Sip Bridging, Voice AI Infra, Voice AI Agents, Voice Models(STT, "
        "TTS)",
    )

    STATUS_CHOICES = [
        ("Requested", "Requested"),
        ("Processing", "Processing"),
        ("Done", "Done"),
    ]
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="Requested"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    product_id = models.CharField(max_length=100, default="unpod.ai")

    def save(self, *args, **kwargs):
        # If registered_as_user is being set to True and it wasn't True before
        if self.registered_as_user and not self.user_register_date:
            self.user_register_date = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.email})"
