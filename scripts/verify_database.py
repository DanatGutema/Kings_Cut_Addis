"""Verify PostgreSQL schema matches SQLAlchemy models."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running as: python scripts/verify_database.py
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import inspect, text

from app.database import Base, engine
from app.models import (  # noqa: F401 — register all models
    AuditLog,
    Customer,
    CustomerSession,
    LoyaltyRule,
    Promotion,
    PromotionRecipient,
    RefreshToken,
    Reward,
    RewardHistory,
    Service,
    ServiceOrder,
    ServiceOrderItem,
    SmsLog,
    Staff,
    SystemSetting,
    TelegramLog,
    Visit,
    VisitService,
)

EXPECTED_TABLES = sorted(Base.metadata.tables.keys())

REQUIRED_COLUMNS: dict[str, list[str]] = {
    "loyalty_rules": [
        "id",
        "rule_name",
        "rule_type",
        "visit_threshold",
        "spending_threshold",
        "reward_type",
        "reward_percentage",
        "reward_amount",
        "expiry_days",
        "evaluation_period_days",
        "is_active",
        "created_at",
        "updated_at",
    ],
}


def main() -> int:
    print("Kings Cut Addis — Database Verification")
    print("=" * 44)

    # 1. Connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[OK] Database connection")
    except Exception as exc:
        print(f"[FAIL] Database connection: {exc}")
        return 1

    # 2. Tables
    inspector = inspect(engine)
    db_tables = sorted(inspector.get_table_names())
    missing = set(EXPECTED_TABLES) - set(db_tables)
    extra = set(db_tables) - set(EXPECTED_TABLES)

    if missing:
        print(f"[FAIL] Missing tables: {sorted(missing)}")
        return 1
    print(f"[OK] All {len(EXPECTED_TABLES)} expected tables exist")

    if extra:
        print(f"[INFO] Extra tables in DB (not in models): {sorted(extra)}")

    # 3. Foreign keys
    fk_count = 0
    for table in EXPECTED_TABLES:
        fk_count += len(inspector.get_foreign_keys(table))
    print(f"[OK] {fk_count} foreign keys found")

    # 4. Key columns (post-migration check)
    for table, columns in REQUIRED_COLUMNS.items():
        db_cols = {c["name"] for c in inspector.get_columns(table)}
        missing_cols = set(columns) - db_cols
        if missing_cols:
            print(f"[FAIL] {table} missing columns: {sorted(missing_cols)}")
            print("       Run: database/migrations/001_add_evaluation_period_and_constraints.sql")
            return 1
    print("[OK] Required columns present (loyalty_rules.evaluation_period_days)")

    # 5. Unique constraint on promotion_recipients
    uniques = inspector.get_unique_constraints("promotion_recipients")
    has_promo_unique = any(
        set(u.get("column_names", [])) == {"promotion_id", "customer_id"}
        for u in uniques
    )
    if has_promo_unique:
        print("[OK] promotion_recipients UNIQUE(promotion_id, customer_id)")
    else:
        print("[WARN] Missing uq_promotion_recipient — run migration 001")

    # 6. Model relationships smoke test
    assert Customer.visits.property.mapper is not None
    assert Visit.customer.property.mapper is not None
    print("[OK] SQLAlchemy relationships load correctly")

    print("=" * 44)
    print("Verification complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
