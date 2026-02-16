from django.core.management import BaseCommand

from unpod.core_components.models import Model


class Command(BaseCommand):
    help = "Update models with necessary data transformations."

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.MIGRATE_HEADING(f"Updating models Startups' statuses")
        )

        models = Model.objects.all()

        for model in models:
            print("Processing pilot:", model.id, model.name)
            model.codename = model.name
            model.save()
