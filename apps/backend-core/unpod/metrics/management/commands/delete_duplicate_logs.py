from django.core.management.base import BaseCommand
from django.db.models import Count
from django.db import transaction
from unpod.metrics.models import CallLog


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        duplicates = (
            CallLog.objects.values(
                "bridge",
                "organization",
                "start_time",
                "source_number",
                "destination_number",
                "end_time",
            )
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )

        self.stdout.write(f"Found {len(duplicates)} duplicate groups")

        with transaction.atomic():
            for dup in duplicates:
                records = CallLog.objects.filter(
                    bridge=dup["bridge"],
                    organization=dup["organization"],
                    start_time=dup["start_time"],
                    source_number=dup["source_number"],
                    destination_number=dup["destination_number"],
                    end_time=dup["end_time"],
                ).order_by(
                    "id"
                )  # keep the first
                records.exclude(id=records.first().id).delete()

        self.stdout.write("✅ Duplicates removed successfully.")
