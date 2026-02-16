"""
Phase 3.3: Management command to set up Django-Q schedules for metrics background tasks.

Run this command once after deployment to configure recurring metrics calculations:
    python manage.py setup_metrics_schedules
"""

from django.core.management.base import BaseCommand
from django_q.models import Schedule


class Command(BaseCommand):
    help = "Set up Django-Q schedules for metrics background tasks"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.MIGRATE_HEADING("Setting up metrics calculation schedules...")
        )

        schedules_created = 0
        schedules_updated = 0

        # Schedule 1: Process uncalculated call logs every 10 minutes
        schedule_1, created = Schedule.objects.update_or_create(
            name='process_uncalculated_call_logs',
            defaults={
                'func': 'unpod.metrics.tasks.process_uncalculated_call_logs',
                'schedule_type': Schedule.MINUTES,
                'minutes': 10,
                'kwargs': '{"batch_size": 100}',
                'repeats': -1,  # Repeat indefinitely
            }
        )
        if created:
            schedules_created += 1
            self.stdout.write(
                self.style.SUCCESS(
                    "✓ Created schedule: process_uncalculated_call_logs (every 10 minutes)"
                )
            )
        else:
            schedules_updated += 1
            self.stdout.write(
                self.style.WARNING(
                    "→ Updated schedule: process_uncalculated_call_logs (every 10 minutes)"
                )
            )

        # Schedule 2: Full metrics recalculation daily at 2 AM
        schedule_2, created = Schedule.objects.update_or_create(
            name='recalculate_all_organization_metrics',
            defaults={
                'func': 'unpod.metrics.tasks.recalculate_all_organization_metrics',
                'schedule_type': Schedule.DAILY,
                'repeats': -1,  # Repeat indefinitely
                'next_run': None,  # Will run at 2 AM based on cron
                'cron': '0 2 * * *',  # Daily at 2 AM
            }
        )
        if created:
            schedules_created += 1
            self.stdout.write(
                self.style.SUCCESS(
                    "✓ Created schedule: recalculate_all_organization_metrics (daily at 2 AM)"
                )
            )
        else:
            schedules_updated += 1
            self.stdout.write(
                self.style.WARNING(
                    "→ Updated schedule: recalculate_all_organization_metrics (daily at 2 AM)"
                )
            )

        # Summary
        self.stdout.write("")
        self.stdout.write(
            self.style.MIGRATE_HEADING("Schedule Setup Complete:")
        )
        self.stdout.write(
            self.style.SUCCESS(f"  • {schedules_created} new schedules created")
        )
        self.stdout.write(
            self.style.WARNING(f"  • {schedules_updated} existing schedules updated")
        )
        self.stdout.write("")
        self.stdout.write(
            self.style.MIGRATE_LABEL("Next Steps:")
        )
        self.stdout.write(
            "  1. Ensure Django-Q cluster is running: sudo systemctl status django-q-qa4"
        )
        self.stdout.write(
            "  2. Start cluster if needed: sudo systemctl start django-q-qa4"
        )
        self.stdout.write(
            "  3. Monitor task execution: python manage.py qmonitor"
        )
        self.stdout.write(
            "  4. Check logs: journalctl -u django-q-qa4 -f"
        )
        self.stdout.write("")
        self.stdout.write(
            self.style.MIGRATE_HEADING("Configured Schedules:")
        )
        self.stdout.write(
            "  • process_uncalculated_call_logs: Every 10 minutes"
        )
        self.stdout.write(
            "    - Processes CallLog records with calculated=False"
        )
        self.stdout.write(
            "    - Batch size: 100 logs per run"
        )
        self.stdout.write(
            "    - Moves expensive aggregations off request path"
        )
        self.stdout.write("")
        self.stdout.write(
            "  • recalculate_all_organization_metrics: Daily at 2 AM"
        )
        self.stdout.write(
            "    - Full metrics recalculation for all organizations"
        )
        self.stdout.write(
            "    - Ensures data consistency"
        )
        self.stdout.write(
            "    - Runs during off-peak hours"
        )
        self.stdout.write("")
