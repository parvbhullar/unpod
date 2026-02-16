from django.core.management.base import BaseCommand
from unpod.thread.crons import fetch_create_cron_post
from django.core.cache import cache


class Command(BaseCommand):
    help = "Generate Post Via Cron Model"

    def handle(self, *args, **options):
        check_key = cache.get("check_cron_post")
        if check_key and check_key == "1":
            self.stdout.write(
                self.style.SUCCESS("Cron Post Generation is already in progress")
            )
            return
        cache.set("check_cron_post", "1")
        fetch_create_cron_post()
        self.stdout.write(self.style.SUCCESS("Successfully generated Posts"))
        self.stdout.write(
            self.style.SUCCESS("*************END OF GENERATION ***************\n\n")
        )
        cache.set("check_cron_post", "0")
