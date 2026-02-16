from django.core.management import BaseCommand

from unpod.subscription.models import ActiveSubscription
from unpod.subscription.services import send_active_sub_reset_reminders


class Command(BaseCommand):
    help = "Process call logs based on filters or parameters"

    def add_arguments(self, parser):
        # Positional argument
        parser.add_argument("act_sub_id", type=str, help="Active Subscription ID")

        parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help="Number of records to process (default: 10)",
        )

        # Optional flag (boolean switch)
        parser.add_argument(
            "--dry-run", action="store_true", help="Run without making database changes"
        )

    def handle(self, *args, **options):
        act_sub_id = options["act_sub_id"]
        limit = options["limit"]
        dry_run = options["dry_run"]

        print("act_sub_id", act_sub_id, limit, dry_run)
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"Filtering calls with Active Subscription ID: {act_sub_id}"
            )
        )

        active_sub = (
            ActiveSubscription.objects.filter(pk=act_sub_id)
            .select_related(
                "user",
                "organization",
            )
            .first()
        )

        send_active_sub_reset_reminders(active_sub)
