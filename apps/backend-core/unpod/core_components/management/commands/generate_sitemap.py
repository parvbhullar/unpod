from django.core.management.base import BaseCommand
from unpod.common.sitemap_generator.sitemap import generate_sitemap


class Command(BaseCommand):
    help = "Generate sitemap"

    def handle(self, *args, **options):
        generate_sitemap()
        self.stdout.write(self.style.SUCCESS("Successfully generated sitemap"))
        self.stdout.write(self.style.SUCCESS("*************END OF GENERATION ***************\n\n"))
