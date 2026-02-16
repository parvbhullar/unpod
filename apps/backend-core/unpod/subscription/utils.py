from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from unpod.common.helpers.document_helper import generate_pdf_from_html
from unpod.common.helpers.service_helper import send_email
from unpod.common.utils import get_global_configs, get_app_info


def send_mail_request_subscription(user, subscription):
    app = get_app_info(subscription.product_id)
    APP_NAME = app.get("APP_NAME")

    subject = f"New {subscription.name} Plan Request - {APP_NAME}"
    email_from = settings.EMAIL_FROM_ADDRESS
    recipient_list = ["subrat@unpod.ai", "babulalkumawat83@gmail.com"]
    context = {
        "user": user,
        "subscription": subscription,
        **app,
    }

    html_content = render_to_string("emails/subscription_request.html", context)

    send_email(
        subject,
        email_from,
        recipient_list,
        mail_body=html_content,
        mail_type="html",
    )


def mail_invoice_to_admin(invoice):
    app = get_app_info(invoice.product_id)
    APP_NAME = app.get("APP_NAME")

    subject = f"New Invoice #{invoice.invoice_number} Generated - {APP_NAME}"
    email_from = settings.EMAIL_FROM_ADDRESS
    email_recipient = get_global_configs("email-recipient")
    recipient_list = email_recipient.get("new_invoice", [])
    invoice_url = f"{settings.BASE_URL}/{settings.ADMIN_URL}/subscription/subscriptioninvoice/{invoice.id}/change/"

    context = {
        "invoice": invoice,
        "sub_total": float(invoice.amount) - float(invoice.tax_amount),
        "invoice_url": invoice_url,
        **app,
    }

    html_file_template = "emails/subscription/admin_invoice_notification.html"
    if invoice.charge_type == "addon_subscription":
        html_file_template = "emails/subscription/admin_addon_invoice_notification.html"

    html_content = render_to_string(html_file_template, context)

    send_email(
        subject,
        email_from,
        recipient_list,
        mail_body=html_content,
        mail_type="html",
    )


def mail_invoice_to_user(invoice):
    app = get_app_info(invoice.product_id)
    APP_NAME = app.get("APP_NAME")

    subject = f"Your Invoice #{invoice.invoice_number} from {APP_NAME}"
    email_from = settings.EMAIL_FROM_ADDRESS
    email_recipient = get_global_configs("email-recipient")
    recipient_list = email_recipient.get("new_invoice", [])
    billing_info = invoice.organization.billing_infos.filter(default=True).first()

    if billing_info and hasattr(billing_info, "email") and billing_info.email:
        recipient_list.append(billing_info.email)

    else:
        role = invoice.organization.organizationmemberroles_organization.filter(
            role__role_code="owner", user__is_active=True
        ).first()
        if role and hasattr(role.user, "email") and role.user.email:
            recipient_list.append(role.user.email)

    context = {
        "invoice": invoice,
        **app,
    }

    payment_term_days = (
        (invoice.due_date - invoice.invoice_date).days
        if invoice.due_date and invoice.invoice_date
        else settings.INVOICE_DUE_DAYS
    )

    act_subscription = invoice.act_subscription
    subscription = act_subscription.subscription_metadata.get("subscription_details")
    app_details = get_global_configs("app_details")

    html_file_template = "emails/subscription/subscription_invoice_email.html"
    if invoice.charge_type == "addon_subscription":
        html_file_template = "emails/subscription/addon_subscription_invoice_email.html"

    html_content = render_to_string(html_file_template, context)

    pdf_context = {
        "invoice": invoice,
        "sub_total": float(invoice.amount) - float(invoice.tax_amount),
        "payment_term_days": payment_term_days,
        "organization": invoice.organization,
        "subscription": subscription,
        "billing_info": billing_info,
        "app_details": app_details,
    }

    pdf_file_template = "pdf/subscription_invoice_template.html"
    if invoice.charge_type == "addon_subscription":
        pdf_file_template = "pdf/addon_subscription_invoice_template.html"

    pdf_html_content = render_to_string(pdf_file_template, pdf_context)
    pdf_file = generate_pdf_from_html(pdf_html_content)

    send_email(
        subject,
        email_from,
        recipient_list,
        mail_body=html_content,
        mail_type="html",
        attachments=[
            {
                "filename": f"Invoice_{invoice.invoice_number}.pdf",
                "content": pdf_file.read(),
                "mimetype": "application/pdf",
            }
        ],
    )


def send_invoice_email(invoice):
    mail_invoice_to_admin(invoice)
    mail_invoice_to_user(invoice)


def send_subscription_reset_reminder_email(
    active_sub, recipient_name=None, recipient_list=None
):
    """
    Send subscription reset reminder email to organization owner or user

    Args:
        active_sub: ActiveSubscription instance
        recipient_name: Optional; Name of the recipient
        recipient_list: Optional; List of recipient email addresses
    """
    app = get_app_info(active_sub.product_id)
    APP_URL = app.get("APP_URL")
    APP_NAME = app.get("APP_NAME")

    subject = f"Subscription Notification - {APP_NAME}"
    email_from = settings.EMAIL_FROM_ADDRESS

    subscription_details = active_sub.subscription_metadata.get(
        "subscription_details", {}
    )
    subscription_name = subscription_details.get("name", "Your Subscription")

    # If no recipient found, skip sending email
    if not recipient_list:
        return False, "No recipient email found"

    context = {
        "recipient_name": recipient_name,
        "subscription_name": subscription_name,
        "days_left": (active_sub.valid_to - timezone.now()).days,
        "reset_date": active_sub.valid_to,
        "billing_url": f"{APP_URL}/billing/",
        **app,
    }

    html_content = render_to_string(
        "emails/subscription/subscription_reset_reminder.html", context
    )

    try:
        sent_count, error = send_email(
            subject,
            email_from,
            recipient_list,
            mail_body=html_content,
            mail_type="html",
        )
        return sent_count > 0, error
    except Exception as e:
        return False, str(e)


def send_channel_limit_reached_email(channel_detail):
    """
    Send email notification when all allocated channels are consumed

    Args:
        channel_detail: ActiveSubscriptionDetail instance for channels
    """
    app = get_app_info(channel_detail.product_id)
    APP_URL = app.get("APP_URL")
    APP_NAME = app.get("APP_NAME")

    subject = f"Channel Limit Reached - {APP_NAME}"
    email_from = settings.EMAIL_FROM_ADDRESS

    subscription_details = channel_detail.act_subscription.subscription_metadata.get(
        "subscription_details", {}
    )
    subscription_name = subscription_details.get("name", "Your Subscription")
    recipient_name = None
    organization = channel_detail.organization

    # Get organization owner email
    recipient_list = []
    billing_info = organization.billing_infos.filter(default=True).first()

    if billing_info and hasattr(billing_info, "email") and billing_info.email:
        recipient_list.append(billing_info.email)
        if not recipient_name:
            recipient_name = billing_info.contact_person or "Valued Customer"
    else:
        role = organization.organizationmemberroles_organization.filter(
            role__role_code="owner", user__is_active=True
        ).first()
        if role and hasattr(role.user, "email") and role.user.email:
            recipient_list.append(role.user.email)
            recipient_name = (
                role.user.get_full_name() or role.user.username or "Valued Customer"
            )

    # If no recipient found, skip sending email
    if not recipient_list:
        return False, "No recipient email found"

    context = {
        "recipient_name": recipient_name or "Valued Customer",
        "subscription_name": subscription_name,
        "billing_url": f"{APP_URL}/billing/",
        **app,
    }

    html_content = render_to_string(
        "emails/subscription/channel_limit_reached.html", context
    )

    try:
        sent_count, error = send_email(
            subject,
            email_from,
            recipient_list,
            mail_body=html_content,
            mail_type="html",
        )
        return sent_count > 0, error
    except Exception as e:
        return False, str(e)
