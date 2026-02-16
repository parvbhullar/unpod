from django_cron import CronJobBase, Schedule
from unpod.wallet.services import processGenerateHistory


class GenerateTaskTransactionHistory(CronJobBase):
    RUN_EVERY_MINS = 60

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "wallet_GenerateTaskTransactionHistory"  # a unique code

    def do(self):
        message = processGenerateHistory()
        return message
