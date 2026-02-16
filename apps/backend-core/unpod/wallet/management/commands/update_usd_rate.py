from django.core.management.base import BaseCommand
from unpod.common.sitemap_generator.sitemap import generate_sitemap
from unpod.wallet.services import updateUSDRate


class Command(BaseCommand):
    help = "Generate sitemap"

    def handle(self, *args, **options):
        message = updateUSDRate()
        self.stdout.write(self.style.HTTP_INFO(message))
        self.stdout.write(self.style.SUCCESS("Successfully generated sitemap"))
        self.stdout.write(
            self.style.SUCCESS("*************END OF GENERATION ***************\n\n")
        )
