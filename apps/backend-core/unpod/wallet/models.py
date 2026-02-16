from django.conf import settings
from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from unpod.common.datetime import get_datetime_now
from unpod.common.mixin import CreatedUpdatedMixin
from unpod.common.query import generate_new_number
from unpod.space.models import SpaceOrganization
from unpod.users.models import User
from unpod.wallet.enum import (
    CurrencyEnum,
    BitsTransactionType,
    BitsTransactionVia,
    PaymentMethodEnum,
    TransactionEnum,
    ChargeTypes,
)


class BitConvertorModel(models.Model):
    unit_value = models.DecimalField(default=75, decimal_places=6, max_digits=20)
    currency = models.CharField(
        max_length=10, choices=CurrencyEnum.choices(), default=CurrencyEnum.INR.name
    )

    def __str__(self):
        return f"{self.unit_value} - {self.currency}"


class Order(CreatedUpdatedMixin):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="%(class)s_user",
        null=True,
        blank=True,
    )
    organization = models.ForeignKey(
        SpaceOrganization,
        on_delete=models.SET_NULL,
        related_name="%(class)s_organization",
        null=True,
        blank=True,
    )

    order_metadata = models.JSONField(default=dict, blank=True, null=True)
    order_number = models.CharField(max_length=20, blank=True, null=True)
    order_type = models.CharField(
        max_length=50, choices=ChargeTypes.choices(), default=ChargeTypes.credits.name
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(choices=CurrencyEnum.choices(), max_length=20)

    notes = models.JSONField(default=dict, blank=True)
    receipt_number = models.CharField(max_length=20, blank=True, null=True)

    payment_mode = models.CharField(
        max_length=20, choices=PaymentMethodEnum.choices(), blank=True, null=True
    )

    online_order_id = models.CharField(max_length=250, blank=True, null=True)
    order_date = models.DateTimeField(blank=True, null=True)

    order_status = models.CharField(
        max_length=50,
        choices=TransactionEnum.choices(),
        default=TransactionEnum.created.name,
    )

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            # Generate a new invoice number if not set
            last_invoice = (
                Order.objects.filter(receipt_number__isnull=False).order_by("id").last()
            )
            if last_invoice and last_invoice.receipt_number:
                last_number = last_invoice.receipt_number
            else:
                last_number = ""

            if "ORDER" in last_number:
                last_number = last_number.replace("ORDER", "").replace("2025", "")

            self.receipt_number = generate_new_number(
                last_number, prefix="RE-", digits=7
            )

        super().save(*args, **kwargs)


class PaymentGatewayTransactions(CreatedUpdatedMixin):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="%(class)s_user",
        null=True,
        blank=True,
    )
    organization = models.ForeignKey(
        SpaceOrganization,
        on_delete=models.SET_NULL,
        related_name="%(class)s_organization",
        null=True,
        blank=True,
    )
    order_id = models.CharField(max_length=250, blank=True, null=True, db_index=True)
    payment_id = models.CharField(max_length=250, blank=True, null=True, db_index=True)
    subscription_id = models.CharField(
        max_length=250, blank=True, null=True, db_index=True
    )
    amount = models.DecimalField(
        default=0, decimal_places=6, max_digits=20, db_index=True
    )
    currency = models.CharField(
        max_length=10, choices=CurrencyEnum.choices(), db_index=True
    )
    payment_mode = models.CharField(
        max_length=50,
        choices=PaymentMethodEnum.choices(),
        default=PaymentMethodEnum.razorpay.name,
        db_index=True,
    )

    status = models.CharField(
        max_length=50,
        choices=TransactionEnum.choices(),
        default=TransactionEnum.created.name,
        db_index=True,
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class TransactionOrder(CreatedUpdatedMixin):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="%(class)s_user",
        null=True,
        blank=True,
    )
    organization = models.ForeignKey(
        SpaceOrganization,
        on_delete=models.SET_NULL,
        related_name="%(class)s_organization",
        null=True,
        blank=True,
    )
    order_number = models.CharField(max_length=20, blank=True, null=True)
    amount = models.DecimalField(default=0, decimal_places=6, max_digits=20)
    currency = models.CharField(choices=CurrencyEnum.choices(), max_length=20)
    order_data = models.JSONField(
        default=dict, blank=True, null=True, encoder=DjangoJSONEncoder
    )
    reason = models.TextField(blank=True, null=True)


class BitsTransaction(CreatedUpdatedMixin):
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="%(class)s_parent",
        null=True,
        blank=True,
        default=None,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="%(class)s_user",
        null=True,
        blank=True,
    )
    organization = models.ForeignKey(
        SpaceOrganization,
        on_delete=models.SET_NULL,
        related_name="%(class)s_organization",
        null=True,
        blank=True,
    )
    order = models.ForeignKey(
        TransactionOrder,
        related_name="%(class)s_order",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    transaction_type = models.CharField(
        max_length=20, default=0, choices=BitsTransactionType.choices()
    )
    transaction_via = models.CharField(
        max_length=20, default=1, choices=BitsTransactionVia.choices()
    )
    transaction_date = models.DateTimeField(blank=True, null=True)
    bits = models.DecimalField(default=0, decimal_places=6, max_digits=20)
    currency_value = models.DecimalField(default=0, decimal_places=6, max_digits=20)
    currency = models.CharField(
        choices=CurrencyEnum.choices(), max_length=20, null=True, blank=True
    )

    def __str__(self):
        return str(self.id) + " - " + str(self.transaction_type)


class UserWallet(CreatedUpdatedMixin):
    bits = models.DecimalField(default=0, decimal_places=6, max_digits=20)
    last_tranaction = models.ForeignKey(
        BitsTransaction,
        on_delete=models.SET_NULL,
        related_name="%(class)s_last_tranaction",
        null=True,
        blank=True,
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="user_wallet",
        null=True,
        blank=True,
    )
    organization = models.ForeignKey(
        SpaceOrganization,
        on_delete=models.SET_NULL,
        related_name="%(class)s_organization",
        null=True,
        blank=True,
    )

    def add_credits(
        self, amount, currency_value, transaction_type, transaction_via, user, currency
    ):
        transaction = BitsTransaction.objects.create(
            user=user,
            organization=self.organization,
            transaction_type=transaction_type,
            transaction_via=transaction_via,
            bits=amount,
            currency_value=currency_value,
            currency=currency,
            transaction_date=get_datetime_now(),
        )
        self.bits += amount
        self.last_tranaction = transaction
        self.save()

        return self.bits


class PaymentGatewayCustomer(CreatedUpdatedMixin):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="%(class)s_user",
        null=True,
        blank=True,
    )
    payment_mode = models.CharField(
        max_length=50,
        choices=PaymentMethodEnum.choices(),
        default=PaymentMethodEnum.razorpay.name,
    )
    customer_id = models.CharField(max_length=99, blank=True, null=True)
    customer_data = models.JSONField(
        default=dict, blank=True, null=True, encoder=DjangoJSONEncoder
    )
