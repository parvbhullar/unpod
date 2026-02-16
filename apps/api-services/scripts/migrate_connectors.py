"""
Migration script: PostgreSQL connector table -> MongoDB connectors collection.

Usage:
    python scripts/migrate_connectors.py

Reads from: PostgreSQL `connector` table (using POSTGRES_CONFIG from settings)
Writes to: MongoDB `connectors` collection (using Mongomantic ConnectorModel)

Idempotent: skips connectors that already exist in MongoDB (by name+source).
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.storage.postgres import executeQuery
from services.store_service.models.connector import ConnectorModel


def migrate_connectors():
    print("Fetching connectors from PostgreSQL...")
    rows = executeQuery(
        "SELECT id, name, source, input_type, connector_specific_config, "
        "refresh_freq, prune_freq, disabled, time_created, time_updated "
        "FROM connector ORDER BY id",
        many=True,
    )

    if not rows:
        print("No connectors found in PostgreSQL.")
        return

    print(f"Found {len(rows)} connectors in PostgreSQL.")

    migrated = 0
    skipped = 0
    errors = 0

    for row in rows:
        name = row["name"]
        source = str(row["source"])

        existing = ConnectorModel.find_one(name=name, source=source)
        if existing:
            print(f"  SKIP: {name} ({source}) — already exists in MongoDB")
            skipped += 1
            continue

        try:
            doc = {
                "name": name,
                "source": source,
                "input_type": str(row.get("input_type", "load_state")),
                "connector_specific_config": row.get("connector_specific_config", {})
                or {},
                "refresh_freq": row.get("refresh_freq"),
                "prune_freq": row.get("prune_freq"),
                "disabled": row.get("disabled", False),
            }
            ConnectorModel.save_single_to_db(doc)
            print(f"  OK: {name} ({source})")
            migrated += 1
        except Exception as e:
            print(f"  ERROR: {name} ({source}) — {e}")
            errors += 1

    print(
        f"\nMigration complete: {migrated} migrated, {skipped} skipped, {errors} errors"
    )


if __name__ == "__main__":
    migrate_connectors()
