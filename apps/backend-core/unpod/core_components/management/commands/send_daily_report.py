from django.core.management.base import BaseCommand
from unpod.core_components.reports.daily import dailyActivityReport


class Command(BaseCommand):
    help = "Send Daily Report"

    def handle(self, *args, **options):
        dailyActivityReport()
        self.stdout.write(self.style.SUCCESS("Successfully sent daily report"))
        self.stdout.write(
            self.style.SUCCESS(
                "*************END OF dailyActivityReport***************\n\n"
            )
        )
