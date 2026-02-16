from django.core.management.base import BaseCommand

from unpod.common.datetime import get_datetime_now, get_days_in_month
import logging

from unpod.subscription.cron import updateCallLogConsumption

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run all scheduled updates for subscriptions, wallets, and transactions"

    def add_arguments(self, parser):
        # Optional: Add command line arguments here if needed
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run in dry-run mode without making any changes",
        )

    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.SUCCESS("Starting scheduled updates..."))

            # Run all updates
            # success, message = run_all_updates()
            #
            # if success:
            #     self.stdout.write(self.style.SUCCESS(message))
            # else:
            #     self.stderr.write(self.style.ERROR(message))

            updateCallLogConsumption()
            now = get_datetime_now()
            curr_month_days = get_days_in_month(now.year, now.month)
            # resetActiveSubscriptions()
            # expireActiveSubscriptions()

            print(f"Current month has {curr_month_days} days. current time: {now}")

        except Exception as e:
            error_msg = f"Error running updates: {str(e)}"
            logger.exception(error_msg)
            self.stderr.write(self.style.ERROR(error_msg))
