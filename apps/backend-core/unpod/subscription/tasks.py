"""
Django-Q2 tasks for subscription app
Migrated from django_cron
"""
import logging
from datetime import timedelta

from django.db import transaction
from django.db.models import Q

from unpod.common.datetime import get_datetime_now
from unpod.subscription.models import ActiveSubscription
from unpod.subscription.services import (
    get_subscription_consumption,
    add_subscription_usage_history,
    calculate_consumption,
    calculateVoiceMinutes,
    send_active_sub_reset_reminders,
)

logger = logging.getLogger(__name__)


def update_call_log_consumption():
    """
    Update call-log minutes for all active subscriptions
    Runs every 5 minutes
    """
    try:
        logger.info("Starting call-log minutes update")

        # Get all active subscriptions with organization prefetched
        active_subs = ActiveSubscription.objects.filter(
            is_active=True,
            expired=False,
            act_sub_detail__codename="voice_minutes",
        ).select_related("organization")  # Prefetch organization to reduce queries

        count = 0
        for active_sub in active_subs.iterator(chunk_size=500):
            logger.debug(f"Active Subscription ID: {active_sub.id}")

            with transaction.atomic():
                try:
                    calculateVoiceMinutes(active_sub)
                    count += 1
                except Exception as e:
                    logger.error(
                        f"Error updating subscription {active_sub.id}: {str(e)}",
                        exc_info=True,
                    )

        logger.info(f"End call-log minutes update. Updated {count} subscriptions")
        return f"Updated {count} subscriptions"
    except Exception as e:
        logger.exception(f"Error in update_call_log_consumption: {e}")
        raise


def reset_active_subscriptions():
    """
    Reset usage for active subscriptions at the start of a new billing cycle
    Part of ProcessEndedSubscriptionsCronJob - runs daily at 00:00
    """
    try:
        logger.info("Starting active subscription resets")
        now = get_datetime_now()

        # Find active subscriptions that need to be reset
        active_subscriptions_to_reset = ActiveSubscription.objects.filter(
            expired=False,
            act_sub_detail__reset_date__lte=now,
        ).distinct()

        count = 0
        for active_sub in active_subscriptions_to_reset.iterator(chunk_size=500):
            with transaction.atomic():
                try:
                    calculate_consumption(active_sub)
                    (
                        consumption,
                        amount,
                        tax_amount,
                        discount,
                        from_date,
                        to_date,
                    ) = get_subscription_consumption(active_sub, reset=True)
                    add_subscription_usage_history(
                        active_sub,
                        from_date,
                        to_date,
                        consumption,
                        amount,
                        tax_amount,
                        discount,
                    )

                    active_sub.renew(to_date)
                    count += 1

                    logger.info(
                        f"Reset usage for subscription {active_sub.id} for user {active_sub.user_id}"
                    )

                except Exception as e:
                    logger.error(f"Error resetting subscription {active_sub.id}: {str(e)}")

        logger.info(f"Completed active subscription resets. Reset {count} subscriptions")
        return f"Reset {count} subscriptions"
    except Exception as e:
        logger.exception(f"Error in reset_active_subscriptions: {e}")
        raise


def expire_active_subscriptions():
    """
    Expire active subscriptions that have ended
    Part of ProcessEndedSubscriptionsCronJob - runs daily at 00:00
    """
    try:
        logger.info("Starting subscription expiration")

        # Find subscriptions that have deactivated but not yet marked as expired
        ended_subscriptions = ActiveSubscription.objects.filter(
            is_active=False, expired=False
        )

        count = 0
        for active_sub in ended_subscriptions.iterator(chunk_size=500):
            with transaction.atomic():
                try:
                    # Mark subscription as expired
                    active_sub.expire()
                    count += 1

                    logger.info(
                        f"Expired subscription {active_sub.id} for user {active_sub.user_id}"
                    )

                except Exception as e:
                    logger.error(f"Error expiring subscription {active_sub.id}: {str(e)}")

        logger.info(f"Completed subscription expiration. Expired {count} subscriptions")
        return f"Expired {count} subscriptions"
    except Exception as e:
        logger.exception(f"Error in expire_active_subscriptions: {e}")
        raise


def process_ended_subscriptions():
    """
    Process ended subscriptions - reset and expire
    Runs daily at 00:00
    Combines reset_active_subscriptions and expire_active_subscriptions
    """
    try:
        logger.info("Starting all scheduled subscription updates")
        reset_result = reset_active_subscriptions()
        expire_result = expire_active_subscriptions()
        logger.info("Completed all scheduled subscription updates")
        return f"Reset: {reset_result}, Expired: {expire_result}"
    except Exception as e:
        logger.exception(f"Error in process_ended_subscriptions: {e}")
        raise


def send_subscription_reset_reminders():
    """
    Send notifications to users 5 days and 2 days before subscription reset date
    Runs daily at 09:00
    """
    try:
        logger.info("Starting subscription reset reminders")
        now = get_datetime_now()
        reminder_date = now - timedelta(days=5)
        reminder_before_2days = now - timedelta(days=2)

        # Find subscription details with reset_date 5 days from now
        # We'll check for reset dates within a range to account for the daily cron execution
        start_range = reminder_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_range = start_range + timedelta(days=1)

        start_range_2days = reminder_before_2days.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_range_2days = start_range_2days + timedelta(days=1)

        active_subscriptions_to_reset = (
            ActiveSubscription.objects.filter(
                is_active=True,
                expired=False,
            )
            .filter(
                Q(valid_to__gte=start_range, valid_to__lte=end_range)
                | Q(valid_to__gte=start_range_2days, valid_to__lte=end_range_2days)
            )
            .select_related(
                "user",
                "organization",
            )
            .distinct()
        )

        count = 0
        for active_sub in active_subscriptions_to_reset.iterator(chunk_size=500):
            with transaction.atomic():
                send_active_sub_reset_reminders(active_sub)
                count += 1

        logger.info(f"Completed subscription reset reminders. Sent {count} reminders")
        return f"Sent {count} reminders"
    except Exception as e:
        logger.exception(f"Error in send_subscription_reset_reminders: {e}")
        raise
