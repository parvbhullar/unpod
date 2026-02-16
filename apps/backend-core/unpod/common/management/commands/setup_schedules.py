"""
Management command to set up Django-Q2 scheduled tasks
Replaces django_cron jobs with Django-Q2 schedules
"""
from django.core.management.base import BaseCommand
from django_q.models import Schedule


class Command(BaseCommand):
    help = "Set up Django-Q2 scheduled tasks (migrated from django_cron)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Setting up Django-Q2 schedules..."))

        schedules = [
            # Wallet - Transaction History (every 60 minutes)
            {
                "name": "wallet_generate_transaction_history",
                "func": "unpod.wallet.tasks.generate_task_transaction_history",
                "schedule_type": Schedule.MINUTES,
                "minutes": 60,
                "repeats": -1,  # -1 = infinite
            },
            # Thread - Create Cron Posts (every 1 minute)
            {
                "name": "thread_create_cron_post",
                "func": "unpod.thread.tasks.create_cron_post",
                "schedule_type": Schedule.MINUTES,
                "minutes": 1,
                "repeats": -1,
            },
            # Core Components - Event Trigger (every 1 minute)
            {
                "name": "core_event_trigger_cron",
                "func": "unpod.core_components.tasks.event_trigger_cron",
                "schedule_type": Schedule.MINUTES,
                "minutes": 1,
                "repeats": -1,
            },
            # Subscription - Update Call Log Consumption (every 5 minutes)
            {
                "name": "subscription_update_call_log_consumption",
                "func": "unpod.subscription.tasks.update_call_log_consumption",
                "schedule_type": Schedule.MINUTES,
                "minutes": 5,
                "repeats": -1,
            },
            # Subscription - Process Ended Subscriptions (daily at 00:00)
            {
                "name": "subscription_process_ended_subscriptions",
                "func": "unpod.subscription.tasks.process_ended_subscriptions",
                "schedule_type": Schedule.CRON,
                "cron": "0 0 * * *",  # Daily at midnight
                "repeats": -1,
            },
            # Subscription - Send Reset Reminders (daily at 09:00)
            {
                "name": "subscription_send_reset_reminders",
                "func": "unpod.subscription.tasks.send_subscription_reset_reminders",
                "schedule_type": Schedule.CRON,
                "cron": "0 9 * * *",  # Daily at 9 AM
                "repeats": -1,
            },
        ]

        created_count = 0
        updated_count = 0

        for schedule_data in schedules:
            name = schedule_data.pop("name")
            schedule, created = Schedule.objects.update_or_create(
                name=name, defaults=schedule_data
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Created schedule: {name}")
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Updated schedule: {name}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n{created_count} schedules created, {updated_count} schedules updated"
            )
        )
        self.stdout.write(
            self.style.WARNING(
                "\nIMPORTANT: Start Django-Q2 cluster with: python manage.py qcluster"
            )
        )
