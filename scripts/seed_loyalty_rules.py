"""Seed default loyalty rules."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from app.database import SessionLocal
from app.models.loyalty_rule import LoyaltyRule

DEFAULT_RULES = [
    {
        "rule_name": "10 Visits Reward",
        "rule_type": "visit",
        "visit_threshold": 10,
        "reward_type": "percentage",
        "reward_percentage": Decimal("15.00"),
        "expiry_days": 30,
        "evaluation_period_days": 90,
    },
    {
        "rule_name": "5000 ETB Spender",
        "rule_type": "spending",
        "spending_threshold": Decimal("5000.00"),
        "reward_type": "fixed",
        "reward_amount": Decimal("500.00"),
        "expiry_days": 60,
        "evaluation_period_days": 180,
    },
]


def main() -> int:
    db = SessionLocal()
    try:
        created = 0
        for data in DEFAULT_RULES:
            if db.scalar(select(LoyaltyRule).where(LoyaltyRule.rule_name == data["rule_name"])):
                continue
            db.add(LoyaltyRule(**data))
            created += 1
        db.commit()
        print(f"Seeded {created} loyalty rule(s). Skipped existing ones.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
