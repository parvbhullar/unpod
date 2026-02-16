from django.contrib import admin
from import_export.admin import ImportExportActionModelAdmin

from unpod.common.mixin import UnpodCustomModelAdmin
from unpod.wallet.models import (
    BitConvertorModel,
    BitsTransaction,
    Order,
    PaymentGatewayCustomer,
    PaymentGatewayTransactions,
    TransactionOrder,
    UserWallet,
)

# Register your models here.


@admin.register(BitConvertorModel)
class BitConvertorModelAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ("unit_value", "currency")
    list_per_page = 20


@admin.register(UserWallet)
class UserWalletAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ("user", "organization", "bits", "created")
    list_per_page = 20


@admin.register(BitsTransaction)
class BitsTransactionAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = (
        "user",
        "organization",
        "transaction_type",
        "transaction_via",
        "transaction_date",
        "bits",
        "created",
    )
    list_filter = (
        "transaction_type",
        "transaction_via",
    )
    list_per_page = 20


@admin.register(PaymentGatewayTransactions)
class CustomPaymentTransactions(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = (
        "user",
        "organization",
        "payment_id",
        "order_id",
        "amount",
        "currency",
        "payment_mode",
        "status",
        "created",
    )
    search_fields = (
        "user__email",
        "payment_id",
        "order_id",
    )
    list_filter = (
        "status",
        "currency",
        "payment_mode",
    )
    list_per_page = 20


@admin.register(Order)
class OrderAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = (
        "user",
        "order_number",
        "online_order_id",
        "amount",
        "currency",
        "order_type",
        "receipt_number",
        "payment_mode",
        "order_date",
        "order_status",
    )
    list_filter = (
        "payment_mode",
        "order_status",
        "order_type",
        "currency",
    )
    list_per_page = 20
    list_editable = ["order_type"]  # editable directly in list


@admin.register(TransactionOrder)
class TransactionOrderAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ("user", "organization", "order_number", "amount")
    list_per_page = 20


@admin.register(PaymentGatewayCustomer)
class PaymentGatewayCustomerAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = (
        "user",
        "customer_id",
        "payment_mode",
    )
    list_filter = ("payment_mode",)
    list_per_page = 20
