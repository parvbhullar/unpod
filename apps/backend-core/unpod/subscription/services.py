import copy
import logging
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import DurationField, ExpressionWrapper, Sum, F, Count, Q

from unpod.common.datetime import get_datetime_now, get_days_in_month
from unpod.common.helpers.calculation_helper import extract_number
from unpod.metrics.models import CallLog, Metrics
from unpod.notification.constants import NOTIFICATION_MESSAGE_EVENT
from unpod.notification.services import createNotification
from unpod.subscription.models import (
    ActiveSubscription,
    ActiveSubscriptionDetail,
    SubscriptionInvoice,
    SubscriptionUsageHistory,
    Subscription,
)
from unpod.subscription.utils import (
    send_invoice_email,
    send_subscription_reset_reminder_email,
    send_channel_limit_reached_email,
)
from unpod.telephony.models import VoiceBridgeNumber

logger = logging.getLogger(__name__)


class SubscriptionService:
    """
    Service to handle subscription related operations
    """

    def __init__(self, organization=None, product_id=None):
        """
        Initialize the service with active subscription and domain handle

        Args:
            organization: The SpaceOrganization instance
            product_id: Optional product ID to filter by
        """
        self.organization = organization
        self.active_subscription = SubscriptionService.get_active_subscription(
            organization=organization, product_id=product_id
        )
        self.subscription = (
            self.active_subscription.subscription if self.active_subscription else None
        )

    def is_subscription_active(self):
        """
        Check if the user or organization has an active subscription

        Returns:
            bool: True if active subscription exists, False otherwise
        """

        if not self.active_subscription:
            return False

        return self.active_subscription.is_active_in_period()

    def get_consumed_channels(self, product_id):
        """
        Get the consumed channels for the organization

        Returns:
            int: Consumed channels or 0 if not found
        """
        try:
            consumed = (
                VoiceBridgeNumber.objects.filter(
                    bridge__organization=self.organization,
                    bridge__product_id=product_id,
                )
                .aggregate(total=models.Sum("channels_count"))
                .get("total")
                or 0
            )

            return consumed

        except Exception as e:
            logger.error(f"Error getting consumed channels: {str(e)}", exc_info=True)
            return 0

    @classmethod
    def get_active_subscription(cls, organization, product_id=None):
        """
        Get the active subscription for a user or organization

        Args:
            organization: The SpaceOrganization instance
            product_id: Optional product ID to filter by

        Returns:
            ActiveSubscription or None
        """
        if not organization:
            return None

        qs = ActiveSubscription.objects.filter(
            organization=organization,
            product_id=product_id,
            is_active=True,
            expired=False,
        )

        return qs.first()

    def update_consumed_channels(self, new_count=0):
        """
        Update the consumed channels in SubscriptionConsumption based on current active channels

        Args:
            new_count (int): Number of new channels to add to consumed count

        Returns:
            tuple: (updated: bool, message: str)
        """
        try:
            actSubDetail = ActiveSubscriptionDetail.objects.filter(
                act_subscription=self.active_subscription, codename="channels"
            ).first()

            if not actSubDetail:
                return False, "No subscription detail found for channels"

            allocated = actSubDetail.allocated
            consumed = self.get_consumed_channels(
                actSubDetail.product_id
            )  # Recalculate consumed channels
            consumed += new_count

            if not actSubDetail.is_unlimited and consumed > allocated:
                return False, "Consumed channels exceed allocated limit"

            actSubDetail.consumed = consumed
            actSubDetail.save(update_fields=["consumed"])

            # Check if all channels are now consumed and send email notification
            if not actSubDetail.is_unlimited and consumed >= allocated:
                try:
                    send_channel_limit_reached_email(actSubDetail)
                except Exception as email_error:
                    print(f"Failed to send channel limit email: {str(email_error)}")

            return True, f"Updated consumed channels to {consumed}"
        except Exception as e:
            logger.error(f"Error updating channel consumption: {str(e)}", exc_info=True)
            return False, f"Error updating channel consumption: {str(e)}"


def find_by_codename(modules, codename):
    return next(
        (data for data in modules if data.get("codename", "") == codename), None
    )


def get_subscription_modules(subscription):
    modules = {}
    subscription_modules = subscription.subscriptionmodules_subscription.all()

    for sub_module in subscription_modules:
        if not sub_module.module:
            print(f"Warning: No module found for subscription plan {sub_module.id}")
            continue

        module_id = sub_module.module.id
        module_name = sub_module.module.name
        codename = sub_module.module.codename
        display_name = sub_module.display_name
        is_unlimited = sub_module.is_unlimited
        quantity = sub_module.quantity
        price_type = sub_module.price_type
        include_in_billing = sub_module.include_in_billing
        tax_percentage = sub_module.tax_percentage
        cost = sub_module.cost
        unit_name = sub_module.module.unit

        module_data = {
            "module_id": module_id,
            "name": module_name,
            "codename": codename,
            "display_name": display_name,
            "is_unlimited": is_unlimited,
            "quantity": quantity,
            "price_type": price_type,
            "unit": unit_name,
            "tax_percentage": (
                float(tax_percentage)
                if isinstance(tax_percentage, Decimal)
                else tax_percentage
            ),
            "tax_code": sub_module.tax_code,
            "cost": (float(cost) if isinstance(cost, Decimal) else cost),
            "include_in_billing": include_in_billing,
        }
        modules[module_name] = module_data

    return modules


def prepare_subscription_metadata(subscription):
    metadata = {
        "modules": get_subscription_modules(subscription),
        "subscription_details": get_subscription_info(subscription),
    }

    return metadata


def get_subscription_info(subscription):
    price = float(subscription.price)
    discount = float(subscription.discount)
    final_price = price - discount if discount < price else 0.0

    metadata = {
        "id": subscription.id,
        "name": subscription.name,
        "tagline": subscription.tagline,
        "description": subscription.description,
        "price": price,
        "discount": discount,
        "final_price": final_price,
        "currency": subscription.currency,
        "type": subscription.type,
        "product_id": subscription.product_id,
    }

    return metadata


def get_voice_usage_stats(active_sub):
    """
    Calculate voice usage statistics using database aggregation for performance.
    Uses a single database query with conditional aggregation instead of loading
    all records into memory.
    """
    now = get_datetime_now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Use database aggregation with conditional Sum for optimal performance
    # This replaces the previous Python-based loop that loaded all records into memory
    stats = CallLog.objects.filter(
        organization=active_sub.organization,
        product_id=active_sub.product_id,
        start_time__gte=month_start,
        start_time__lte=now,
        call_duration__isnull=False,
    ).exclude(
        call_duration=timedelta(0)
    ).aggregate(
        # Total duration for the month
        month_total=Sum(
            ExpressionWrapper(F('call_duration'), output_field=DurationField())
        ),
        # Total duration for today only (using conditional aggregation)
        today_total=Sum(
            ExpressionWrapper(F('call_duration'), output_field=DurationField()),
            filter=Q(start_time__gte=today_start)
        )
    )

    # Convert durations to seconds, handling None values
    month_duration = stats.get('month_total')
    today_duration = stats.get('today_total')

    month_seconds = month_duration.total_seconds() if month_duration else 0
    today_seconds = today_duration.total_seconds() if today_duration else 0

    # Round up to nearest minute
    today_minutes = (today_seconds + 59) // 60
    month_minutes = (month_seconds + 59) // 60

    return {
        "today_minutes": int(today_minutes),
        "month_minutes": int(month_minutes),
    }


def calculateVoiceMinutes(active_sub):
    """
    Calculate total voice minutes for a given active subscription
    """
    # Get current total consumed minutes from ActiveSubscriptionDetail
    actSubDetail = ActiveSubscriptionDetail.objects.filter(
        act_subscription=active_sub, codename="voice_minutes"
    ).first()

    if actSubDetail is None:
        print(f"No ActiveSubscriptionDetail for subscription {active_sub.id}, skipping")
        return

    # Get incremental usage for the specified interval with call count
    call_logs_query = CallLog.objects.filter(
        organization=active_sub.organization,
        product_id=active_sub.product_id,
        calculated=False,
        call_duration__isnull=False,
        # start_time__gte=active_sub.valid_from,
        # start_time__lte=active_sub.valid_to,
    )
    ids = list(call_logs_query.values_list("id", flat=True))

    if not ids:
        print(f"No new call logs for subscription {active_sub.id}")
        return

    stats = CallLog.objects.filter(id__in=ids).aggregate(
        total=Sum(ExpressionWrapper(F("call_duration"), output_field=DurationField())),
        call_count=Count("id"),
    )

    # Convert to seconds (if total_duration is not None)
    totalSeconds = stats.get("total", 0).total_seconds()
    newTotalMinutes = (totalSeconds + 59) // 60  # Round up to nearest minute
    currentTotalMinutes = actSubDetail.consumed or 0
    totalMinutes = currentTotalMinutes + newTotalMinutes

    # Update new total consumed minutes in ActiveSubscriptionDetail
    actSubDetail.consumed = F("consumed") + newTotalMinutes
    print(
        f"Updating voice minutes for subscription {active_sub.id}: +{newTotalMinutes} mins, total {totalMinutes} mins"
    )
    actSubDetail.save()

    # update call logs flag
    CallLog.objects.filter(id__in=ids).update(calculated=True)

    # Update Metrics
    Metrics.objects.filter(
        organization=active_sub.organization,
        product_id=active_sub.product_id,
        name="Total Cost",
    ).update(value=totalMinutes)


def calculate_consumption(active_sub):
    """
    Calculate consumption for all modules in the active subscription
    """

    "calculate voice minutes"
    calculateVoiceMinutes(active_sub)


def get_subscription_consumption(active_sub, reset=False):
    calculate_consumption(active_sub)

    now = get_datetime_now().replace(hour=0, minute=0, second=0, microsecond=0)
    curr_month_days = get_days_in_month(now.year, now.month)

    # Also reset details in ActiveSubscriptionDetail
    details = ActiveSubscriptionDetail.objects.filter(act_subscription=active_sub)

    consumption = {}
    total_tax = float(0)
    total_amount = float(0)
    reset_date = now
    next_reset_date = now + timedelta(days=curr_month_days)

    for detail in details:
        reset_date = detail.reset_date
        next_reset_date = detail.reset_date + timedelta(days=curr_month_days)
        tax_percentage = float(detail.tax_percentage)

        # Initialize variables
        cost = float(detail.cost)

        # fixed price modules or unlimited modules charge only base price
        if detail.is_unlimited or detail.price_type == "fixed":
            extra_consumed = 0
            extra_amount = 0
            extra_tax_amount = 0
            extra_total_amount = detail.get_extra_total()
            amount = cost

        else:
            # per unit modules
            extra_consumed = max(0, int(detail.consumed) - int(detail.allocated))
            extra_amount = extra_consumed * cost
            extra_tax_amount = extra_amount * (tax_percentage / 100)
            extra_total_amount = detail.get_extra_total()

            total_consumed = detail.allocated + extra_consumed
            amount = total_consumed * cost

        # Calculate tax and total
        tax_amount = amount * (tax_percentage / 100)
        total_module_amount = detail.get_total()

        # Aggregate totals
        total_tax += tax_amount
        total_amount += total_module_amount

        # Prepare module consumption data
        module_consumption = {
            "module_id": detail.module_id,
            "codename": detail.codename,
            "display_name": detail.display_name,
            "allocated": detail.allocated,
            "consumed": detail.consumed,
            "unit": detail.unit,
            "price_type": detail.price_type,
            "cost": cost,
            "tax_percentage": tax_percentage,
            "amount": amount,
            "tax_amount": tax_amount,
            "total_amount": total_module_amount,
            "extra_usage": {
                "consumed": extra_consumed,
                "amount": extra_amount,
                "tax_amount": extra_tax_amount,
                "total_amount": extra_total_amount,
            },
            "is_unlimited": detail.is_unlimited,
            "include_in_billing": detail.include_in_billing,
        }

        consumption[detail.module.name] = module_consumption

        if reset:
            detail.reset(next_reset_date)

    # Ensure at least the base price is charged
    subscription_details = active_sub.subscription_metadata.get(
        "subscription_details", {}
    )

    price = subscription_details.get("price", 0)
    discount = subscription_details.get("discount", 0)
    final_price = subscription_details.get("final_price", price)

    total_amount = total_amount if total_amount > 0 else final_price

    return consumption, total_amount, total_tax, discount, reset_date, next_reset_date


def get_extra_consumption(active_sub):
    """
    Get only the extra consumption for all modules in the active subscription
    """

    calculate_consumption(active_sub)

    # Also reset details in ActiveSubscriptionDetail
    details = ActiveSubscriptionDetail.objects.filter(
        act_subscription=active_sub, price_type="per_unit"
    )

    now = get_datetime_now()
    from_date = now
    to_date = now

    consumption = {}
    total_tax = float(0)
    total_amount = float(0)

    for detail in details:
        from_date = detail.reset_date
        extra_consumed = max(0, int(detail.consumed) - int(detail.allocated))
        if extra_consumed > 0:
            cost = float(detail.cost)
            tax_percentage = float(detail.tax_percentage)

            amount = extra_consumed * cost
            tax_amount = amount * (tax_percentage / 100)
            total_module_amount = detail.get_extra_total()

            total_tax += tax_amount
            total_amount += total_module_amount

            consumption[detail.module.name] = {
                "module_id": detail.module_id,
                "codename": detail.codename,
                "display_name": detail.display_name,
                "allocated": detail.allocated,
                "consumed": detail.consumed,
                "unit": detail.unit,
                "price_type": detail.price_type,
                "cost": cost,
                "tax_percentage": tax_percentage,
                "amount": amount,
                "tax_amount": tax_amount,
                "total_amount": total_module_amount,
                "is_unlimited": detail.is_unlimited,
                "include_in_billing": detail.include_in_billing,
            }

    return consumption, total_amount, total_tax, from_date, to_date


def create_invoice(
    active_sub,
    consumption,
    amount=0.00,
    tax_amount=0.00,
    discount=0.00,
    history=None,
    order=None,
    charge_type="subscription",
    status="pending",
    notes="Auto-generated invoice",
):
    now = get_datetime_now()
    # Create invoice record
    due_date = now + timedelta(days=settings.INVOICE_DUE_DAYS)  # 7 days to pay
    invoice = SubscriptionInvoice.objects.create(
        act_subscription=active_sub,
        organization=active_sub.organization,
        product_id=active_sub.product_id,
        usage_history=history,
        order=order,
        invoice_date=now,
        due_date=due_date,
        total_usage=consumption,
        charge_type=charge_type,
        status=status,
        notes=notes,
        amount=amount,
        tax_amount=tax_amount,
        discount=discount,
        payment_at=now if status == "paid" else None,
    )

    return invoice


def add_subscription_invoice(
    active_sub,
    consumption,
    amount=0.00,
    tax_amount=0.00,
    discount=0.00,
    history=None,
    order=None,
    status="pending",
    notes="Auto-generated invoice",
):
    # Create invoice record
    invoice = create_invoice(
        active_sub,
        consumption,
        amount=amount,
        tax_amount=tax_amount,
        discount=discount,
        history=history,
        order=order,
        status=status,
        notes=notes,
    )

    send_invoice_email(invoice)

    return invoice


def add_subscription_aadons_invoice(
    active_sub,
    consumption,
    amount=0.00,
    tax_amount=0.00,
    order=None,
    status="pending",
    notes="Auto-generated invoice",
):
    # Create invoice record
    invoice = create_invoice(
        active_sub,
        consumption,
        amount=amount,
        tax_amount=tax_amount,
        discount=0.00,
        order=order,
        charge_type="addon_subscription",
        status=status,
        notes=notes,
    )

    send_invoice_email(invoice)

    return invoice


def add_subscription_usage_history(
    active_sub,
    from_date,
    to_date,
    consumption,
    amount=0.00,
    tax_amount=0.00,
    discount=0.00,
):
    month = from_date.replace(hour=0, minute=0, second=0, microsecond=0)

    # Create usage history record
    history = SubscriptionUsageHistory.objects.create(
        act_subscription=active_sub,
        organization=active_sub.organization,
        product_id=active_sub.product_id,
        consumption_metadata=consumption,
        from_date=from_date,
        to_date=to_date,
        month=month,
        amount=amount,
    )

    status = "pending" if amount > 0 else "paid"

    add_subscription_invoice(
        active_sub,
        consumption,
        amount=amount,
        tax_amount=tax_amount,
        discount=discount,
        history=history,
        status=status,
    )

    return history


def expire_active_subscription(curr_act_sub):
    """
    Expires all other active subscriptions for the same organization and product_id
    except the current active subscription.
    """

    filterDate = {
        "organization_id": curr_act_sub.organization.id,
        "product_id": curr_act_sub.product_id,
        "is_active": True,
        "expired": False,
    }

    active_subscriptions = ActiveSubscription.objects.filter(**filterDate).exclude(
        id=curr_act_sub.id
    )

    for active_sub in active_subscriptions:
        (
            consumption,
            amount,
            tax_amount,
            from_date,
            to_date,
        ) = get_extra_consumption(active_sub)

        if amount > 0:
            add_subscription_usage_history(
                active_sub,
                from_date,
                to_date,
                consumption,
                amount,
                tax_amount,
                discount=0.00,
            )
        active_sub.expire()

    return True


def add_active_subscription_detail(act_sub, modules):
    act_sub_detail_data = []
    consumption = {}
    total_amount = float(0)
    total_tax = float(0)
    consumption_count = 0
    reset_date = act_sub.valid_to
    warning_threshold = 80

    for module_name, details in modules.items():
        allocated = details.get("quantity", 0)
        unit = details.get("unit", "")
        price_type = details.get("price_type", "per_unit")
        cost = float(details.get("cost", 0))
        tax_percentage = float(details.get("tax_percentage", 0))
        tax_code = details.get("tax_code", "")
        module_id = details.get("module_id", None)
        codename = details.get("codename", module_name.lower().replace(" ", "_"))
        display_name = details.get("display_name", module_name)
        is_unlimited = details.get("is_unlimited", False)
        include_in_billing = details.get("include_in_billing", True)

        act_sub_detail_data.append(
            ActiveSubscriptionDetail(
                act_subscription=act_sub,
                organization=act_sub.organization,
                product_id=act_sub.product_id,
                module_id=module_id,
                codename=codename,
                display_name=display_name,
                allocated=allocated,
                consumed=0,
                unit=unit,
                price_type=price_type,
                cost=cost,
                tax_percentage=tax_percentage,
                tax_code=tax_code,
                is_unlimited=is_unlimited,
                include_in_billing=include_in_billing,
                warning_threshold=warning_threshold,
                reset_date=reset_date,
                created_by=act_sub.user,
            )
        )

        if is_unlimited or price_type == "fixed":
            amount = cost
        else:
            amount = allocated * cost

        tax_amount = amount * (tax_percentage / 100)  # assuming 20% VAT
        total_module_amount = amount + tax_amount
        total_amount += total_module_amount
        total_tax += tax_amount

        consumption[module_name] = {
            "module_id": module_id,
            "codename": codename,
            "display_name": display_name,
            "allocated": allocated,
            "consumed": 0,
            "unit": unit,
            "price_type": price_type,
            "cost": cost,
            "tax_percentage": tax_percentage,
            "tax_code": tax_code,
            "amount": amount,
            "tax_amount": tax_amount,
            "total_amount": total_module_amount,
            "is_unlimited": is_unlimited,
            "include_in_billing": include_in_billing,
        }

        consumption_count += 1

    if consumption_count == 0:
        print("No consumption data to insert.")
    else:
        # Insert all in one query
        ActiveSubscriptionDetail.objects.bulk_create(act_sub_detail_data)

    return consumption, total_amount, total_tax


def createActiveSubscription(
    subscription, user, organization=None, order=None, metadata=None
):
    if metadata is None:
        metadata = {}
    start_date = get_datetime_now()
    curr_month_days = get_days_in_month(start_date.year, start_date.month)
    end_date = start_date + timedelta(days=curr_month_days)

    active_subscription = ActiveSubscription.objects.create(
        user=user,
        subscription=subscription,
        organization=organization,
        product_id=subscription.product_id,
        is_active=True,
        valid_from=start_date,
        valid_to=end_date,
        subscription_metadata=metadata,
    )

    # Expire any previous active subscriptions for the same product
    expire_active_subscription(active_subscription)

    # Get subscription_details and modules from metadata
    subscription_details = metadata.get("subscription_details")
    modules = metadata.get("modules")

    if modules:
        consumption, total_amount, total_tax = add_active_subscription_detail(
            active_subscription, modules
        )

        # Ensure at least the base price is charged
        price = subscription_details.get("price", 0)
        discount = subscription_details.get("discount", 0)
        final_price = subscription_details.get("final_price", price)

        total_amount = total_amount if total_amount > 0 else final_price

        add_subscription_invoice(
            active_subscription,
            consumption,
            amount=total_amount,
            tax_amount=total_tax,
            discount=discount,
            order=order,
            status="paid",
            notes="Initial invoice for subscription activation",
        )

    return active_subscription


def assign_default_subscription(product_id, user, organization):
    """
    Assign a default subscription to an organization
    """

    subscription = Subscription.objects.filter(
        is_default=True, is_active=True, product_id=product_id, price=0
    ).first()
    if subscription:
        metadata = prepare_subscription_metadata(subscription)

        active_subscription = createActiveSubscription(
            subscription,
            user,
            organization=organization,
            metadata=metadata,
        )

        return active_subscription

    return None


def assign_addons_to_subscription(addons_modules, act_sub, order_data):
    """
    Assign add-on subscriptions to an existing active subscription
    """

    subscription_details = act_sub.subscription_metadata.get("subscription_details", {})
    order = act_sub.subscription_metadata.get("order", {})
    modules = act_sub.subscription_metadata.get("modules", {})
    history = act_sub.subscription_metadata.get("history", [])

    history.append(
        {
            "date": get_datetime_now().isoformat(),
            "order": copy.deepcopy(order),
            "modules": copy.deepcopy(modules),
            "subscription_details": copy.deepcopy(subscription_details),
        }
    )

    total_tax = float(0)

    for name, module in modules.items():
        codename = module.get("codename", "")
        addon_module = next(
            (
                data
                for data in addons_modules.values()
                if data.get("codename", "") == codename
            ),
            None,
        )
        if addon_module:
            addon_quantity = addon_module.get("quantity", "0")
            module_quantity = module.get("quantity", 0)
            quantity = addon_quantity + module_quantity
            module["quantity"] = quantity
            total_tax += float(addon_module.get("tax_amount", 0))
        else:
            module_quantity = extract_number(module.get("quantity", "0"))
            module["quantity"] = module_quantity

    order_amount = float(order_data.amount)
    price = subscription_details.get("price", 0)
    final_price = subscription_details.get("final_price", price)

    subscription_details["price"] = price + order_amount
    subscription_details["final_price"] = final_price + order_amount

    order["order_id"] = order_data.id
    order["offer_id"] = order_data.order_metadata.get("offer_id", "")
    order["online_order_id"] = order_data.online_order_id
    act_sub.save()

    add_subscription_aadons_invoice(
        act_sub,
        addons_modules,
        amount=order_data.amount,
        tax_amount=total_tax,
        order=order_data,
        status="paid",
        notes="Invoice for add-on subscription purchase",
    )

    return {
        "subscription_details": subscription_details,
        "modules": modules,
        "history": history,
    }


def send_active_sub_reset_reminders(active_sub):
    try:
        recipient_list = []  # Default admin email for testing
        billing_info = active_sub.organization.billing_infos.filter(
            default=True
        ).first()
        role = active_sub.organization.organizationmemberroles_organization.filter(
            role__role_code="owner", user__is_active=True
        ).first()

        user_to = role.user.id if role else active_sub.user.id
        recipient_name = (
            role.user.get_full_name() or role.user.username
            if role
            else "Valued Customer"
        )

        if role and hasattr(role.user, "email") and role.user.email:
            recipient_list.append(role.user.email)

        if billing_info and hasattr(billing_info, "email") and billing_info.email:
            recipient_list.append(billing_info.email)
            recipient_name = billing_info.contact_person or recipient_name

        if not user_to:
            logger.warning(
                f"No recipient found for subscription {active_sub.id}, skipping notification"
            )
        else:
            # Prepare notification data
            subscription_details = active_sub.subscription_metadata.get(
                "subscription_details", {}
            )
            subscription_name = subscription_details.get("name", "Your Subscription")
            reset_date_str = active_sub.valid_to.strftime("%Y-%m-%d %H:%M")

            notification_body = NOTIFICATION_MESSAGE_EVENT[
                "subscription_reset_reminder"
            ].format(
                subscription_name=subscription_name,
                reset_date=reset_date_str,
            )

            # Create notification
            createNotification(
                event="subscription_reset_reminder",
                object_type="subscription",
                user_from="system",
                user_to=user_to,
                title="Subscription Notification",
                body=notification_body,
                event_data={
                    "act_subscription_id": active_sub.id,
                    "subscription_id": subscription_details.get("id"),
                    "reset_date": reset_date_str,
                },
            )

            logger.info(
                f"Sent reset reminder notification for active subscription {active_sub.id} to user {user_to}"
            )

            # Send email with all subscription details
            email_sent, error = send_subscription_reset_reminder_email(
                active_sub,
                recipient_name=recipient_name,
                recipient_list=recipient_list,
            )

            if email_sent:
                logger.info(
                    f"Sent reset reminder email for subscription {active_sub.id}"
                )
            else:
                logger.warning(
                    f"Failed to send email for subscription {active_sub.id}: {error}"
                )

    except Exception as e:
        logger.error(
            f"Error sending reminder for active subscription {active_sub.id}: {str(e)}",
            exc_info=True,
        )
