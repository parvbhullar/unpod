from django.urls import path
from unpod.wallet.views import (
    BitValueViewSet,
    BitsTransactionViewSet,
    RazorPaymentAPI,
    SubscriptionPaymentViewSet,
    UserWalletViewSet,
)

# fmt: off
app_name = "wallet"
urlpatterns = [
    path("detail/", UserWalletViewSet.as_view({"get": "get"}), name="wallet-detail"),
    path("bit-detail/", BitValueViewSet.as_view({"get": "get"}), name="bit-detail"),
    path("bit-transaction/", BitsTransactionViewSet.as_view({"get": "get"}), name="bit-transaction"),
    # Bits Recharge
    path(
        "payment/create-order/",
        RazorPaymentAPI.as_view({"post": "createOrder"}),
        name="razorpay-create-order",
    ),
    path(
        "payment/complete-transaction/",
        RazorPaymentAPI.as_view({"post": "transaction"}),
        name="razorpay-complete-transaction",
    ),
    # Common transaction status API
    path(
        "payment/transaction-status/",
        RazorPaymentAPI.as_view({"put": "put"}),
        name="razorpay-transaction-status",
    ),
    # Subscription API
    path(
        "payment/create-subscription-order/",
        SubscriptionPaymentViewSet.as_view({"post": "createsubscription"}),
        name="create_subscription_order",
    ),
    path(
        "payment/complete-subscription-order/",
        SubscriptionPaymentViewSet.as_view({"post": "complete_subscription"}),
        name="complete_subscription_order",
    ),
    # Add-on Subscription APIs
    path(
        "payment/create-addon-subscription-order/",
        SubscriptionPaymentViewSet.as_view({"post": "create_addon_subscription"}),
        name="create_addon_subscription_order",
    ),
    path(
        "payment/complete-addon-subscription-order/",
        SubscriptionPaymentViewSet.as_view({"post": "complete_addon_subscription"}),
        name="complete_addon_subscription_order",
    ),
    # Invoice Payment APIs
    path(
        "payment/pay-invoice/",
        SubscriptionPaymentViewSet.as_view({"post": "pay_invoice"}),
        name="pay_pending_invoice",
    ),
    path(
        "payment/complete-invoice-payment/",
        SubscriptionPaymentViewSet.as_view({"post": "complete_invoice_payment"}),
        name="complete_invoice_payment",
    ),
    path(
        "check-subscription/",
        SubscriptionPaymentViewSet.as_view({"get": "checkSubscription"}),
        name="check-subscription",
    ),
    path(
        "subscription-detail/",
        SubscriptionPaymentViewSet.as_view({"get": "subscription_detail"}),
        name="subscription-detail",
    ),
    path(
        "payment/complete-subscription-test/",
        SubscriptionPaymentViewSet.as_view({"post": "complete_subscription_demo"}),
        name="complete_subscription_test",
    ),
    path(
        "subscription-cancel/",
        SubscriptionPaymentViewSet.as_view({"post": "cancel_subscription"}),
        name="cancel_subscription",
    ),
    path(
        "subscription-test/",
        SubscriptionPaymentViewSet.as_view({"get": "subscription_test"}),
        name="cancel_test",
    ),
]
