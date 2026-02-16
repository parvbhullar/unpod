from django_cron import CronJobBase, Schedule
from unpod.thread.crons import fetch_create_cron_post
from django.core.cache import cache


class CreateCronPost(CronJobBase):
    RUN_EVERY_MINS = 1

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "thread_CreateCronPost"  # a unique code

    def do(self):
        check_key = cache.get("check_cron_post")
        if check_key and check_key == "1":
            print("Cron Post Generation is already in progress")
            return "Cron Post Generation is already in progress"
        cache.set("check_cron_post", "1")
        message = fetch_create_cron_post()
        print("Successfully generated Posts")
        cache.set("check_cron_post", "0")
        return message
