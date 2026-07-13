"""Apply incremental migrations to an existing database."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import text

from app.database import engine

MIGRATIONS_DIR = ROOT / "database" / "migrations"


def main() -> int:
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        print("No migration files found.")
        return 0

    for path in migration_files:
        sql = path.read_text(encoding="utf-8")
        print(f"Applying {path.name} ...")
        with engine.begin() as conn:
            conn.execute(text(sql))
        print(f"  Done.")

    print("All migrations applied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
