from django.urls import path
from .views import (
    PlanSubscriptionViewSet,
    UserSubscriptionView,
)

# fmt: off

urlpatterns = [
    # Subscription plans (using /plans/ as the single endpoint for listing)
    path(
        'plans/',
        PlanSubscriptionViewSet.as_view({'get': 'subscription_list'}),
        name='subscription-plans',
    ),
    path(
        '<int:id>/',
        PlanSubscriptionViewSet.as_view({'get': 'subscription_details'}),
        name='subscription_details',
    ),

    # Subscription management
    path(
        'request-subscription/',
        PlanSubscriptionViewSet.as_view({"post": "request_subscription"}),
        name="request-subscription",
    ),
    path(
        'user-subscription/',
        UserSubscriptionView.as_view({"get": "get_active_subscription"}),
        name='user-subscription',
    ),
    path(
        'user-invoices/',
        UserSubscriptionView.as_view({"get": "get_invoices"}),
        name='user-invoices',
    ),
    path(
        'user-invoices/<str:invoice_number>/download/',
        UserSubscriptionView.as_view({"get": "download_invoice"}),
        name='user-invoice-download-by-number',
    ),
    path(
        'user-invoices/<str:invoice_number>/email-preview/',
        UserSubscriptionView.as_view({"get": "email_preview"}),
        name='user-invoice-email-preview',
    ),
    # path("email-preview/<int:invoice_id>/", preview_invoice_email, name="preview-invoice-email"),
]
