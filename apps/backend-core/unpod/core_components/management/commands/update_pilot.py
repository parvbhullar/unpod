from django.core.management import BaseCommand

from unpod.core_components.models import Pilot


class Command(BaseCommand):
    help = "Update pilot users based on filters or parameters"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.MIGRATE_HEADING(f"Updating pilot Startups' statuses")
        )

        pilots = Pilot.objects.exclude(telephony_config={}).exclude(
            telephony_config__isnull=True
        )

        for pilot in pilots:
            print(
                "Processing pilot:", pilot.id, pilot.name, type(pilot.telephony_config)
            )
            if type(pilot.telephony_config) is dict:
                telephony = pilot.telephony_config.get("telephony", None)
                if telephony and len(telephony) > 0:
                    numbers_ids = []
                    for number_info in telephony:
                        numbers_ids.append(number_info.get("id"))

                    if numbers_ids:
                        print("Adding numbers:", numbers_ids)
                        pilot.numbers.add(*numbers_ids)
