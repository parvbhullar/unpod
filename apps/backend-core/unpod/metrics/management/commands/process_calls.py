from django.core.management import BaseCommand

from unpod.metrics.models import CallLog


class Command(BaseCommand):
    help = "Process call logs based on filters or parameters"

    def add_arguments(self, parser):
        # Positional argument
        parser.add_argument("token", type=str, help="Organization token")

        # Optional argument
        parser.add_argument(
            "--status", type=str, default="success", help="Call status to filter"
        )

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
        token = options["token"]
        status = options["status"]
        limit = options["limit"]
        dry_run = options["dry_run"]

        print("token", token, status, limit, dry_run)
        self.stdout.write(
            self.style.MIGRATE_HEADING(f"Filtering calls with status: {status}")
        )
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"Filtering calls with Organization token: {token}"
            )
        )
        queryset = CallLog.objects.filter(
            organization__token=token, call_type="outbound"
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING("Dry run mode enabled – no changes will be saved.")
            )

        for call in queryset:
            # self.stdout.write(f"Processing call ID: {call.id}")
            # Mark call as not calculated
            call.calculated = False

            if not dry_run:
                call.save()

        self.stdout.write(self.style.SUCCESS(f"Processed {queryset.count()} calls."))
