"""
Management command to seed reference data (Providers, ModelTypes, Models,
Languages, Voices, VoiceProfiles) from CSV files shipped in seed_data/.

Idempotent: skips if providers already exist. Use --force to re-seed.
"""

import csv
import os

from django.core.management.base import BaseCommand
from django.db import connection

SEED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed_data")

# Order matters: parents first, then children, then M2M junction tables
TABLES = [
    # dynamic_forms needed by provider FK
    "dynamic_forms",
    "dynamic_form_field_options_api",
    "dynamic_form_fields",
    # main tables
    "core_components_provider",
    "core_components_modeltype",
    "core_components_language",
    "core_components_model",
    "core_components_voice",
    "core_components_voiceprofiles",
    # M2M junction tables
    "core_components_model_voice",
    "core_components_model_languages",
    "core_components_model_model_types",
    "core_components_voice_language",
    "core_components_voiceprofiles_stt_language",
    "core_components_voiceprofiles_tts_language",
]


def get_nullable_columns(cursor, table_name):
    """Return set of column names that allow NULL."""
    cursor.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = %s AND is_nullable = 'YES'",
        [table_name],
    )
    return {row[0] for row in cursor.fetchall()}


class Command(BaseCommand):
    help = "Seed core component reference data from CSV files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Re-seed even if data already exists (truncates first)",
        )

    def handle(self, *args, **options):
        force = options["force"]

        with connection.cursor() as cursor:
            # Check if data exists
            cursor.execute("SELECT COUNT(*) FROM core_components_provider")
            count = cursor.fetchone()[0]

            if count > 0 and not force:
                self.stdout.write(
                    f"[seed] Data already exists ({count} providers). "
                    "Use --force to re-seed."
                )
                return

            if force and count > 0:
                self.stdout.write("[seed] Force mode: truncating existing data...")
                for table in reversed(TABLES):
                    cursor.execute(f"TRUNCATE TABLE {table} CASCADE")

            self.stdout.write("[seed] Loading reference data...")

            for table in TABLES:
                csv_path = os.path.join(SEED_DIR, f"{table}.csv")
                if not os.path.exists(csv_path):
                    self.stdout.write(f"  SKIP {table} (no CSV)")
                    continue

                with open(csv_path, "r") as f:
                    reader = csv.reader(f)
                    headers = next(reader)
                    rows = list(reader)

                if not rows:
                    self.stdout.write(f"  SKIP {table} (empty)")
                    continue

                # Find which columns are nullable
                nullable = get_nullable_columns(cursor, table)

                columns = ", ".join(f'"{h}"' for h in headers)
                placeholders = ", ".join(["%s"] * len(headers))

                inserted = 0
                errors = 0
                for row in rows:
                    processed = []
                    for i, val in enumerate(row):
                        col_name = headers[i]
                        if val == "":
                            # NULL for nullable columns, empty string for NOT NULL
                            processed.append(None if col_name in nullable else "")
                        else:
                            processed.append(val)
                    try:
                        cursor.execute(
                            f"INSERT INTO {table} ({columns}) "
                            f"VALUES ({placeholders}) "
                            f"ON CONFLICT DO NOTHING",
                            processed,
                        )
                        inserted += 1
                    except Exception as e:
                        errors += 1
                        if errors <= 3:
                            self.stderr.write(f"  ERROR {table}: {e}")

                # Reset sequence for tables with serial/identity id
                try:
                    cursor.execute(f"""
                        DO $$
                        BEGIN
                            IF EXISTS (
                                SELECT 1 FROM information_schema.columns
                                WHERE table_name='{table}'
                                AND column_name='id'
                                AND data_type IN ('integer','bigint')
                            ) THEN
                                PERFORM setval(
                                    pg_get_serial_sequence('{table}', 'id'),
                                    COALESCE((SELECT MAX(id) FROM {table}), 1)
                                );
                            END IF;
                        END $$;
                    """)
                except Exception:
                    pass

                msg = f"  {table}: {inserted} rows"
                if errors:
                    msg += f" ({errors} errors)"
                self.stdout.write(msg)

        self.stdout.write(self.style.SUCCESS("[seed] Done!"))
