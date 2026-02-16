import hashlib
import json
import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.db.models import Prefetch
from django.shortcuts import render
from django.template.loader import render_to_string
from rest_framework import viewsets, status
from rest_framework.permissions import (
    IsAuthenticated,
)
from rest_framework.response import Response

from unpod.common.renderers import UnpodJSONRenderer
from .models import (
    Subscription,
    ActiveSubscription,
    ActiveSubscriptionDetail,
    SubscriptionRequest,
    SubscriptionInvoice,
)
from .serializers import (
    PlanListSerializer,
    ActiveSubscriptionDetailSerializer,
    SubscriptionInvoiceListSerializer,
)
from .services import get_voice_usage_stats
from .utils import send_mail_request_subscription, send_invoice_email
from ..common.datetime import get_formated_date
from ..common.helpers.document_helper import download_pdf_from_html
from ..common.helpers.global_helper import get_product_id
from ..common.utils import get_email_global_data, get_global_configs
from ..space.services import get_organization_by_domain_handle

logger = logging.getLogger(__name__)


def preview_invoice_email(request, invoice_number):
    invoice = SubscriptionInvoice.objects.get(invoice_number=invoice_number)
    invoice_url = f"{settings.BASE_URL}/{settings.ADMIN_URL}/subscription/subscriptioninvoice/{invoice.id}/change/"
    billing_info = invoice.organization.billing_infos.filter(default=True).first()
    recipients = []

    if billing_info and hasattr(billing_info, "email") and billing_info.email:
        recipients.append(billing_info.email)

    else:
        role = invoice.organization.organizationmemberroles_organization.filter(
            role__role_code="owner", user__is_active=True
        ).first()
        if role and hasattr(role.user, "email") and role.user.email:
            recipients.append(role.user.email)

    context = {
        "invoice": invoice,
        "sub_total": float(invoice.amount) - float(invoice.tax_amount),
        "invoice_url": invoice_url,
        **get_email_global_data(),
    }

    # send_invoice_email(invoice)
    # return render(request, "emails/invoice_email.html", context)

    html_file_template = "emails/subscription/admin_invoice_notification.html"
    if invoice.charge_type == "addon_subscription":
        html_file_template = "emails/subscription/admin_addon_invoice_notification.html"

    return render(request, html_file_template, context)


class UserSubscriptionView(viewsets.GenericViewSet):
    """
    API view to get the current user's subscription details and usage
    """

    permission_classes = [IsAuthenticated]
    renderer_classes = [UnpodJSONRenderer]

    def get_active_subscription(self, request, *args, **kwargs):
        try:
            domain_handle = self.request.headers.get("Org-Handle", None)
            product_id = request.headers.get("Product-Id")
            organization = get_organization_by_domain_handle(domain_handle)

            if not organization:
                return Response(
                    {
                        "message": "Organization not found for the given domain handle",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Check Redis cache first (60 second TTL)
            cache_key = f"user_subscription:{organization.id}:{product_id}"
            cached_response = cache.get(cache_key)
            if cached_response:
                return Response(cached_response, status=status.HTTP_200_OK)

            # Get active subscription with optimized query
            # Use select_related for FK and prefetch_related for reverse FK with module
            actSubscription = ActiveSubscription.objects.filter(
                organization=organization,
                is_active=True,
                expired=False,
                product_id=product_id,
            ).select_related(
                'subscription',
                'organization',
            ).prefetch_related(
                Prefetch(
                    'act_sub_detail',
                    queryset=ActiveSubscriptionDetail.objects.select_related('module')
                )
            ).first()

            if not actSubscription:
                response_data = {
                    "message": "No active subscription found",
                    "data": {
                        "has_subscription": False,
                        "subscription": None,
                        "invoice": {
                            "invoice_number": None,
                            "amount": 0,
                            "invoice_date": None,
                        },
                        "usage_stats": {
                            "today_minutes": 0,
                            "month_minutes": 0,
                        },
                        "modules": [],
                        "allowed_modules": [],
                    },
                }
                return Response(response_data, status=status.HTTP_200_OK)

            modules_metadata = actSubscription.subscription_metadata.get("modules", None)
            subscription = actSubscription.subscription_metadata.get(
                "subscription_details", {}
            )

            plan_name = subscription.get("name", "custom").lower()
            next_billing_date = actSubscription.valid_to + timedelta(days=1)
            subscription_amount = subscription.get("price", 0)

            # Optimized invoice query - use select_related and limit by ID ordering
            invoice = (
                SubscriptionInvoice.objects.filter(act_subscription=actSubscription)
                .order_by("-id")
                .only("invoice_number", "amount", "invoice_date")
                .first()
            )

            invoiceData = {
                "invoice_number": None,
                "amount": subscription_amount,
                "invoice_date": get_formated_date(actSubscription.valid_from),
            }

            if invoice:
                invoiceData = {
                    "invoice_number": invoice.invoice_number,
                    "amount": float(invoice.amount) if invoice.amount else 0,
                    "invoice_date": get_formated_date(invoice.invoice_date),
                }

            allowed_modules = []
            if modules_metadata:
                for feature, details in modules_metadata.items():
                    codename = details.get(
                        "codename", feature.lower().replace(" ", "_")
                    )
                    allowed_modules.append(codename)

            subscription_data = {
                **subscription,
                "plan_name": plan_name,
                "start_date": get_formated_date(actSubscription.valid_from),
                "next_billing_date": get_formated_date(next_billing_date),
            }

            # Use prefetched data - no additional queries needed
            modules = ActiveSubscriptionDetailSerializer(
                actSubscription.act_sub_detail.all(), many=True
            ).data

            response_data = {
                "message": "Subscription details retrieved successfully",
                "data": {
                    "has_subscription": True,
                    "subscription": subscription_data,
                    "invoice": invoiceData,
                    "usage_stats": get_voice_usage_stats(actSubscription),
                    "modules": modules,
                    "allowed_modules": allowed_modules,
                },
            }

            # Cache the response for 60 seconds
            cache.set(cache_key, response_data, 60)

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error fetching subscription details: {str(e)}", exc_info=True)
            return Response(
                {
                    "message": "An error occurred while fetching subscription details",
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get_invoices(self, request, *args, **kwargs):
        try:
            domain_handle = self.request.headers.get("Org-Handle", None)
            product_id = request.headers.get("Product-Id")
            organization = get_organization_by_domain_handle(domain_handle)

            if not organization:
                return Response(
                    {
                        "message": "Organization not found for the given domain handle",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Get year from query params or use current year
            year = request.query_params.get("year")
            if year:
                try:
                    year = int(year)
                except ValueError:
                    return Response(
                        {"status": "error", "message": "Invalid year format. Use YYYY"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                year = datetime.now().year

            # Get all invoice records for the year
            invoices = SubscriptionInvoice.objects.filter(
                organization=organization,
                product_id=product_id,
                invoice_date__year=year,
            ).order_by("-invoice_date")

            invoiceSerializer = SubscriptionInvoiceListSerializer(invoices, many=True)

            return Response(
                {
                    "message": "Invoices fetched successfully",
                    "data": invoiceSerializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {
                    "message": "An error occurred while fetching invoices",
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def download_invoice(self, request, invoice_number):
        """
        Download the invoice PDF for a specific invoice number.
        Args:
            request: The HTTP request
            invoice_number (str): The invoice number to download
        Returns:
            HttpResponse: PDF file response or error message
        """
        try:
            invoice = SubscriptionInvoice.objects.get(invoice_number=invoice_number)
            billing_info = invoice.organization.billing_infos.filter(
                default=True
            ).first()
            act_subscription = invoice.act_subscription
            subscription = act_subscription.subscription_metadata.get(
                "subscription_details"
            )
            app_details = get_global_configs("app_details")

            payment_term_days = (
                (invoice.due_date - invoice.invoice_date).days
                if invoice.due_date and invoice.invoice_date
                else settings.INVOICE_DUE_DAYS
            )

            context = {
                "invoice": invoice,
                "sub_total": invoice.amount - invoice.tax_amount,
                "payment_term_days": payment_term_days,
                "organization": invoice.organization,
                "subscription": subscription,
                "billing_info": billing_info,
                "app_details": app_details,
            }

            html_file_template = "pdf/subscription_invoice_template.html"
            if invoice.charge_type == "addon_subscription":
                html_file_template = "pdf/addon_subscription_invoice_template.html"

            html_string = render_to_string(html_file_template, context)

            return download_pdf_from_html(html_string, f"invoice_{invoice_number}")

        except SubscriptionInvoice.DoesNotExist:
            return Response(
                {"status": "error", "message": "Invoice not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            logger.error(f"Error in download_invoice: {str(e)}", exc_info=True)
            return Response(
                {
                    "status": "error",
                    "message": "An error occurred while downloading the invoice",
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def email_preview(self, request, invoice_number):
        try:
            invoice = SubscriptionInvoice.objects.get(invoice_number=invoice_number)
            send_invoice_email(invoice)  # To generate context for email preview

            return Response(
                {"status": "success", "message": "Invoice email preview generated"},
                status=status.HTTP_200_OK,
            )

        except SubscriptionInvoice.DoesNotExist:
            return Response(
                {"status": "error", "message": "Invoice not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            logger.error(f"Error in email_preview: {str(e)}", exc_info=True)
            return Response(
                {
                    "status": "error",
                    "message": "An error occurred while previewing the email",
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PlanSubscriptionViewSet(viewsets.GenericViewSet):
    """
    ViewSet for handling subscription plans and subscription requests
    """

    permission_classes = [IsAuthenticated]
    serializer_class = PlanListSerializer
    renderer_classes = [UnpodJSONRenderer]

    def subscription_list(self, request, *args, **kwargs):
        # Retrieve and format subscriptions with prefetched modules
        product_id = get_product_id()

        # Optimized query with prefetch_related and only() to fetch required fields
        from .models import SubscriptionModules  # Import here to avoid circular imports

        subscriptions = (
            Subscription.objects.filter(is_active=True, product_id=product_id)
            .prefetch_related(
                models.Prefetch(
                    "subscriptionmodules_subscription",  # Updated to match the related_name
                    queryset=SubscriptionModules.objects.select_related("module").only(
                        "module__id",
                        "module__codename",
                        "included_in_sub",
                        "display_name",
                        "description",
                    ),
                )
            )
            .only(
                "id",
                "name",
                "tagline",
                "help_text",
                "is_popular",
                "description",
                "price",
                "discount",
                "type",
                "is_default",
                "currency",
            )
        )

        plans = []
        for subscription in subscriptions:
            # Get all modules for this subscription from prefetched data
            modules_data = []
            for module in subscription.subscriptionmodules_subscription.all():
                modules_data.append(
                    {
                        "module_id": module.module.id,
                        "codename": module.module.codename,
                        "included_in_sub": module.included_in_sub,
                        "display_name": module.display_name,
                        "description": module.description,
                    }
                )

            price = float(subscription.price)
            discount = float(subscription.discount)
            final_price = price - discount if discount < price else 0.0

            subscription_data = {
                "id": subscription.id,
                "title": subscription.name,
                "plan": subscription.name.lower(),
                "tagline": subscription.tagline,
                "help_text": subscription.help_text,
                "is_popular": subscription.is_popular,
                "description": subscription.description,
                "price": price,
                "discount": discount,
                "final_price": final_price,
                "type": subscription.type,
                "is_default": subscription.is_default,
                "currency": subscription.currency,
                "modules": modules_data,
            }

            plans.append(subscription_data)

        return Response(
            {
                "message": "Subscription plans fetch successfully",
                "data": plans,
            }
        )

    def subscription_details(self, request, id=None, *args, **kwargs):
        try:
            subscription = Subscription.objects.get(id=id, is_active=True)
            serializer = self.get_serializer(subscription)
            return Response(
                {
                    "message": "Subscription plan details fetched successfully",
                    "data": serializer.data,
                }
            )
        except Subscription.DoesNotExist:
            return Response(
                {
                    "message": "Subscription plan not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

    def request_subscription(self, request, *args, **kwargs):
        try:
            plan_id = request.data.get("plan_id")
            if not plan_id:
                return Response(
                    {"message": "Plan ID is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            domain_handle = self.request.headers.get("Org-Handle", None)
            organization = get_organization_by_domain_handle(domain_handle)

            if not organization:
                return Response(
                    {
                        "message": "Organization not found for the given domain handle",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            user = self.request.user
            subscription = Subscription.objects.filter(
                id=request.data.get("plan_id")
            ).first()

            if not subscription:
                return Response(
                    {
                        "message": "Subscription plan not found",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Get product_id from the subscription
            product_id = subscription.product_id

            SubscriptionRequest.objects.create(
                subscription_id=request.data.get("plan_id"),
                user=user,
                organization=organization,
                message=request.data.get("message", ""),
                product_id=product_id,
            )

            send_mail_request_subscription(user, subscription)

            return Response(
                {
                    "message": "Subscription request sent successfully",
                }
            )

        except Subscription.DoesNotExist:
            return Response(
                {
                    "message": "Subscription plan not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            logger.error(f"Error in request_subscription: {str(e)}", exc_info=True)
            return Response(
                {
                    "message": "An error occurred while processing your request",
                    "error": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
