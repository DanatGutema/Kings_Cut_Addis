"""Seed default barber shop services."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from app.database import SessionLocal
from app.models.service import Service

DEFAULT_SERVICES = [
    ("Haircut", Decimal("200.00"), 30),
    ("Beard Trim", Decimal("100.00"), 15),
    ("Shaving", Decimal("80.00"), 15),
    ("Hair Wash", Decimal("50.00"), 10),
    ("Spa Treatment", Decimal("350.00"), 45),
]


def main() -> int:
    db = SessionLocal()
    try:
        created = 0
        for name, price, duration in DEFAULT_SERVICES:
            if db.scalar(select(Service).where(Service.name == name)):
                continue
            db.add(Service(name=name, price=price, duration_minutes=duration))
            created += 1
        db.commit()
        print(f"Seeded {created} service(s). Skipped existing ones.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
