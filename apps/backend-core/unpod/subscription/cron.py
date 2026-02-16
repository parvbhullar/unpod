import logging
from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django_cron import CronJobBase, Schedule

from unpod.common.datetime import get_datetime_now
from unpod.subscription.models import (
    ActiveSubscription,
)
from unpod.subscription.services import (
    get_subscription_consumption,
    add_subscription_usage_history,
    calculate_consumption,
    calculateVoiceMinutes,
    send_active_sub_reset_reminders,
)

logger = logging.getLogger(__name__)


def updateCallLogConsumption():
    """
    Update call-log minutes for all active subscriptions
    """

    # Get all active subscriptions with organization prefetched
    active_subs = ActiveSubscription.objects.filter(
        is_active=True,
        expired=False,
        act_sub_detail__codename="voice_minutes",
    ).select_related(
        "organization"
    )  # Prefetch organization to reduce queries

    for active_sub in active_subs.iterator(chunk_size=500):
        print("Active Subscription ID:", active_sub.id)

        with transaction.atomic():
            try:
                calculateVoiceMinutes(active_sub)
            except Exception as e:
                logger.error(
                    f"Error updating subscription {active_sub.id}: {str(e)}",
                    exc_info=True,
                )


def resetActiveSubscriptions():
    """
    Reset usage for active subscriptions at the start of a new billing cycle
    """
    now = get_datetime_now()
    # curr_month_days = get_days_in_month(now.year, now.month)

    # Find active subscriptions that need to be reset
    active_subscriptions_to_reset = ActiveSubscription.objects.filter(
        expired=False,
        act_sub_detail__reset_date__lte=now,
    ).distinct()

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

                logger.info(
                    f"Reset usage for subscription {active_sub.id} for user {active_sub.user_id}"
                )

            except Exception as e:
                logger.error(f"Error resetting subscription {active_sub.id}: {str(e)}")


def expireActiveSubscriptions():
    """
    Expire active subscriptions that have ended
    """
    # Find subscriptions that have deactivated but not yet marked as expired
    ended_subscriptions = ActiveSubscription.objects.filter(
        is_active=False, expired=False
    )

    for active_sub in ended_subscriptions.iterator(chunk_size=500):
        with transaction.atomic():
            try:
                # Mark subscription as expired
                active_sub.expire()

                logger.info(
                    f"Expired subscription {active_sub.id} for user {active_sub.user_id}"
                )

            except Exception as e:
                logger.error(f"Error expiring subscription {active_sub.id}: {str(e)}")


def sendSubscriptionResetReminders():
    """
    Send notifications to users 5 days before subscription reset date
    """
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

    for active_sub in active_subscriptions_to_reset.iterator(chunk_size=500):
        with transaction.atomic():
            send_active_sub_reset_reminders(active_sub)


class AddCallLogConsumptionCronJob(CronJobBase):
    """
    Cron job to add call log consumption every hour
    """

    # Unique code for the cron job
    code = "unpod.subscription.AddCallLogConsumptionCronJob"

    # Run every 5 minutes
    RUN_EVERY_MINS = 5
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)

    def do(self):
        try:
            logger.info("Starting call-log minutes update")
            # result = send_demo_email()
            # logger.info(f"Demo email result: {result}")
            updateCallLogConsumption()
            logger.info("End call-log minutes update")
        except Exception as e:
            logger.exception(f"[Cron] Unexpected error in {self.code}: {e}")


class ProcessEndedSubscriptionsCronJob(CronJobBase):
    """
    Cron job to process ended subscriptions every day at midnight
    """

    # Unique code for the cron job
    code = "unpod.subscription.ProcessEndedSubscriptionsCronJob"

    # Run every day at midnight
    schedule = Schedule(run_at_times=["00:00"])

    def do(self):
        try:
            logger.info("Starting all scheduled updates")
            resetActiveSubscriptions()
            expireActiveSubscriptions()
            logger.info("Completed all scheduled updates")
        except Exception as e:
            logger.exception(f"[Cron] Unexpected error in {self.code}: {e}")


class SubscriptionResetReminderCronJob(CronJobBase):
    """
    Cron job to send subscription reset reminders 5 days before reset date
    Runs daily at 9:00 AM
    """

    # Unique code for the cron job
    code = "unpod.subscription.SubscriptionResetReminderCronJob"

    # Run every day at 9:00 AM
    schedule = Schedule(run_at_times=["09:00"])

    def do(self):
        try:
            logger.info("Starting subscription reset reminders")
            # sendSubscriptionResetReminders()
            logger.info("Completed subscription reset reminders")
        except Exception as e:
            logger.exception(f"[Cron] Unexpected error in {self.code}: {e}")
