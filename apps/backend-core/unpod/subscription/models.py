from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils import timezone
from faker.utils.text import slugify

from unpod.common.datetime import get_datetime_now
from unpod.common.enum import InvoiceStatus
from unpod.common.mixin import CreatedUpdatedMixin
from unpod.common.query import generate_new_number
from unpod.space.models import SpaceOrganization
from unpod.wallet.enum import CurrencyEnum, SubscriptionTypes, ChargeTypes
from unpod.wallet.models import Order


class PlanModules(CreatedUpdatedMixin):
    name = models.CharField(max_length=99)
    codename = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    unit = models.CharField(max_length=50)
    cost = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, help_text="Cost per unit"
    )
    description = models.TextField(blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.name} - {self.unit}"

    def save(self):
        if self.codename:
            self.codename = slugify(self.codename).replace("-", "_")

        else:
            self.codename = slugify(self.name).replace("-", "_")

        super().save()


class Subscription(CreatedUpdatedMixin):
    name = models.CharField(max_length=99)
    tagline = models.CharField(max_length=199, blank=True, null=True)
    is_popular = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    help_text = models.CharField(max_length=199, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    product_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    type = models.CharField(
        max_length=10,
        choices=SubscriptionTypes.choices(),
        default=SubscriptionTypes.standard.name,
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    custom_data = models.JSONField(
        blank=True, null=True, default=dict, encoder=DjangoJSONEncoder
    )
    currency = models.CharField(
        max_length=10, choices=CurrencyEnum.choices(), default=CurrencyEnum.INR.name
    )
    sort_order = models.PositiveIntegerField(
        default=0, help_text="Order of the plan in listings"
    )

    def __str__(self) -> str:
        return f"{self.name} - {self.price}"

    class Meta:
        ordering = ["sort_order", "price"]


class SubscriptionRequest(models.Model):
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_subscription",
    )
    organization = models.ForeignKey(
        SpaceOrganization,
        on_delete=models.SET_NULL,
        related_name="%(class)s_organization",
        null=True,
        blank=True,
    )
    product_id = models.CharField(max_length=100, blank=True, null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_user",
    )
    message = models.TextField(blank=True, null=True)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.subscription} - {self.user}"


class SubscriptionModules(CreatedUpdatedMixin):
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_subscription",
    )
    module = models.ForeignKey(
        PlanModules,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_module",
    )
    display_name = models.CharField(max_length=99, blank=True, null=True)
    description = models.CharField(max_length=99, blank=True, null=True)
    is_unlimited = models.BooleanField(
        default=False, help_text="If true, consumption is unlimited"
    )
    quantity = models.IntegerField(default=0)
    price_type = models.CharField(
        max_length=10,
        choices=[("fixed", "Fixed"), ("per_unit", "Per Unit")],
        default="fixed",
    )
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=00.00)
    tax_code = models.CharField(
        default="0", max_length=99, help_text="Tax code for categorization"
    )
    included_in_sub = models.BooleanField(
        default=True, help_text="If true, included in subscription"
    )
    include_in_billing = models.BooleanField(
        default=True, help_text="If true, include in billing"
    )
    sort_order = models.PositiveIntegerField(
        default=0, help_text="Order of the module in the subscription"
    )

    def __str__(self) -> str:
        return f"{self.subscription} - {self.module} - {self.quantity}"


class ActiveSubscription(CreatedUpdatedMixin):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_user",
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_subscription",
    )
    product_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    is_active = models.BooleanField(default=True)
    billing_mode = models.CharField(
        max_length=10,
        choices=[("monthly", "Monthly"), ("yearly", "Yearly")],
        default="monthly",
    )
    valid_from = models.DateTimeField(blank=True, null=True)
    valid_to = models.DateTimeField(blank=True, null=True)

    expired = models.BooleanField(default=False)
    expired_on = models.DateTimeField(blank=True, null=True)
    organization = models.ForeignKey(
        SpaceOrganization,
        on_delete=models.SET_NULL,
        related_name="%(class)s_organization",
        null=True,
        blank=True,
    )
    subscription_metadata = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        user_str = str(self.user) if self.user else "[No User]"
        subscription_str = (
            str(self.subscription) if self.subscription else "[No Subscription]"
        )

        return f"{subscription_str} - {user_str}"

    def is_active_in_period(self, date=None):
        """Check if subscription is active for the given date"""
        if date is None:
            date = timezone.now()
        return self.is_active and self.valid_from <= date <= self.valid_to

    def expire(self):
        """Expire the subscription"""
        self.expired = True
        self.expired_on = get_datetime_now()
        self.is_active = False
        self.save()
        return self

    def deactivate(self):
        """Deactivate the subscription without marking it as expired"""
        self.is_active = False
        self.save()
        return self

    def renew(self, to_date=None):
        """
        Renew the subscription to a new end date
        """
        self.valid_to = to_date
        self.expired = False
        self.save()

        return True

    class Meta:
        indexes = [
            models.Index(
                fields=["organization", "is_active", "expired", "product_id"],
                name="act_sub_org_status_idx",
            ),
        ]


class ActiveSubscriptionDetail(models.Model):
    """
    Tracks detailed consumption of active subscription modules with thresholds and limits
    """

    act_subscription = models.ForeignKey(
        ActiveSubscription,
        on_delete=models.CASCADE,
        related_name="act_sub_detail",
        verbose_name="Active Subscription",
    )
    organization = models.ForeignKey(
        SpaceOrganization,
        on_delete=models.SET_NULL,
        null=True,
        related_name="act_sub_detail",
    )
    product_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    module = models.ForeignKey(
        PlanModules,
        on_delete=models.SET_NULL,
        null=True,
        related_name="act_sub_detail",
    )
    codename = models.CharField(
        max_length=50,
        help_text="Codename of the feature (e.g., 'voice_minutes', 'channels')",
    )
    display_name = models.CharField(max_length=99, blank=True, null=True)
    allocated = models.IntegerField(
        default=0, help_text="Total allocated amount for this module"
    )
    consumed = models.IntegerField(default=0, help_text="Amount currently consumed")
    unit = models.CharField(max_length=50, blank=True, help_text="Unit of the module")
    price_type = models.CharField(
        max_length=10,
        choices=[("fixed", "Fixed"), ("per_unit", "Per Unit")],
        default="fixed",
    )
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_percentage = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_code = models.CharField(
        default="0", max_length=99, help_text="Tax code for categorization"
    )
    is_unlimited = models.BooleanField(
        default=False, help_text="If true, consumption is unlimited"
    )
    include_in_billing = models.BooleanField(
        default=True, help_text="If true, include in billing"
    )
    warning_threshold = models.IntegerField(
        default=80, help_text="Percentage threshold for sending warnings (0-100)"
    )
    reset_date = models.DateTimeField(help_text="When this record will be reset")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="act_sub_detail",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("act_subscription", "module")
        verbose_name = "Active Subscription Detail"
        verbose_name_plural = "Active Subscription Details"
        indexes = [
            models.Index(
                fields=["act_subscription", "codename"],
                name="asd_sub_codename_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.act_subscription} - {self.module}: {self.consumed}/{self.allocated}"
        )

    @property
    def remaining(self):
        return max(0, self.allocated - self.consumed)

    def get_total(self):
        """Calculate total cost including base cost and tax"""
        if self.is_unlimited or self.price_type == "fixed":
            base_cost = float(self.cost)
        else:
            extra_usage = max(0, self.consumed - self.allocated)
            base_cost = float(self.cost) * (self.allocated + extra_usage)

        tax_percentage = float(self.tax_percentage)
        tax_amount = (base_cost * tax_percentage) / 100
        return base_cost + tax_amount

    def get_extra_total(self):
        if self.is_unlimited:
            return 0.00

        """Calculate total cost including tax"""
        if self.price_type == "fixed":
            return 0.00

        extra_usage = max(0, self.consumed - self.allocated)
        if extra_usage == 0:
            return 0.00

        extra_cost = float(self.cost) * extra_usage
        tax_percentage = float(self.tax_percentage)
        tax_amount = (extra_cost * tax_percentage) / 100
        return extra_cost + tax_amount

    @property
    def usage_percentage(self):
        if self.allocated == 0:
            return 0
        return (self.consumed / self.allocated) * 100

    def reset(self, reset_date):
        """Reset consumption for a new billing period"""
        self.consumed = 0
        self.reset_date = reset_date
        self.save()
        return self


class SubscriptionUsageHistory(models.Model):
    """
    Tracks historical subscription periods and their usage
    """

    act_subscription = models.ForeignKey(
        ActiveSubscription,
        on_delete=models.CASCADE,
        related_name="sub_usage_history",
        verbose_name="Active Subscription",
    )
    organization = models.ForeignKey(
        SpaceOrganization,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sub_usage_history",
    )
    product_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    consumption_metadata = models.JSONField(default=dict, blank=True)
    from_date = models.DateTimeField()
    to_date = models.DateTimeField()
    month = models.DateTimeField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sub_usage_history",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Subscription Usage History"
        verbose_name_plural = "Subscription Usage Histories"
        ordering = ["-from_date"]

    def __str__(self):
        return f"{self.act_subscription} - {self.from_date.date()} to {self.to_date.date()}"


class SubscriptionInvoice(CreatedUpdatedMixin):
    """
    Tracks historical subscription periods and their usage
    """

    act_subscription = models.ForeignKey(
        ActiveSubscription,
        on_delete=models.CASCADE,
        related_name="invoice",
        verbose_name="Active Subscription",
    )
    organization = models.ForeignKey(
        SpaceOrganization,
        on_delete=models.SET_NULL,
        null=True,
        related_name="subscription_invoice",
    )
    usage_history = models.ForeignKey(
        SubscriptionUsageHistory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoice",
        verbose_name="Usage History",
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoice",
    )
    charge_type = models.CharField(
        max_length=50,
        choices=ChargeTypes.choices(),
        default=ChargeTypes.subscription.name,
    )
    product_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    invoice_number = models.CharField(
        max_length=20, blank=True, null=True, db_index=True
    )
    invoice_date = models.DateTimeField()
    due_date = models.DateTimeField()
    total_usage = models.JSONField(default=dict)  # Stores feature-wise usage
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(
        max_length=10, choices=CurrencyEnum.choices(), default=CurrencyEnum.INR.name
    )
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=50,
        choices=InvoiceStatus.choices(),
        default=InvoiceStatus.pending.name,
    )
    payment_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Subscription Invoices"
        ordering = ["-invoice_date"]
        indexes = [
            models.Index(
                fields=["organization", "product_id", "invoice_date"],
                name="si_org_prod_date_idx",
            ),
        ]

    def __str__(self):
        return f"{self.act_subscription} - {self.invoice_date.date()} to {self.due_date.date()}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Generate a new invoice number if not set
            last_invoice = (
                SubscriptionInvoice.objects.filter(invoice_number__isnull=False)
                .order_by("id")
                .last()
            )
            if last_invoice and last_invoice.invoice_number:
                last_number = last_invoice.invoice_number
            else:
                last_number = ""

            self.invoice_number = generate_new_number(last_number)

        super().save(*args, **kwargs)
