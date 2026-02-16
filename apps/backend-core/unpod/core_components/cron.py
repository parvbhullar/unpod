from django_cron import CronJobBase, Schedule
from unpod.core_components.services import process_event_cron


class EventTriggerCron(CronJobBase):
    RUN_EVERY_MINS = 1

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "core_EventTriggerCron"  # a unique code

    def do(self):
        message = process_event_cron()
        return message
