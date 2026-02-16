from django.core.management import BaseCommand

from unpod.core_components.models import VoiceProfiles


class Command(BaseCommand):
    help = "Update pilot users based on filters or parameters"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.MIGRATE_HEADING(f"Updating pilot Startups' statuses")
        )

        profiles = VoiceProfiles.objects.all()

        for profile in profiles:
            print("Processing profile:", profile.pk, profile.name)

            profile.greeting_message = (
                profile.first_message.encode("utf-8").decode("unicode-escape")
                if profile.first_message
                else ""
            )

            profile.save(update_fields=["greeting_message"])
