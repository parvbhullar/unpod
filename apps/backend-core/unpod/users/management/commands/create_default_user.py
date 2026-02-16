"""
Create a default superuser for local development and open-source contributors.

Idempotent — skips creation if the user already exists.
Credentials can be overridden via environment variables.

Usage:
    python manage.py create_default_user
    python manage.py create_default_user --no-input   # same behaviour, explicit
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

DEFAULT_EMAIL = "admin@unpod.dev"
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin123"


class Command(BaseCommand):
    help = "Create a default superuser for local development (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            default=os.environ.get("DJANGO_DEFAULT_ADMIN_EMAIL", DEFAULT_EMAIL),
            help=f"Admin email (default: {DEFAULT_EMAIL})",
        )
        parser.add_argument(
            "--username",
            default=os.environ.get("DJANGO_DEFAULT_ADMIN_USERNAME", DEFAULT_USERNAME),
            help=f"Admin username (default: {DEFAULT_USERNAME})",
        )
        parser.add_argument(
            "--password",
            default=os.environ.get("DJANGO_DEFAULT_ADMIN_PASSWORD", DEFAULT_PASSWORD),
            help=f"Admin password (default: {DEFAULT_PASSWORD})",
        )

    def handle(self, *args, **options):
        email = options["email"]
        username = options["username"]
        password = options["password"]

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(
                    f"Default user '{username}' already exists — skipping."
                )
            )
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            first_name="Admin",
            last_name="User",
            verify_email=True,
        )

        self.stdout.write(self.style.SUCCESS("\n===================================="))
        self.stdout.write(self.style.SUCCESS("  Default admin user created!"))
        self.stdout.write(self.style.SUCCESS("===================================="))
        self.stdout.write(f"  Email:    {email}")
        self.stdout.write(f"  Username: {username}")
        self.stdout.write(f"  Password: {password}")
        self.stdout.write(f"  Admin:    http://localhost:8000/unpod-admin/")
        self.stdout.write(self.style.SUCCESS("====================================\n"))
