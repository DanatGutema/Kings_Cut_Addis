"""drop unused customers.loyalty_status tier column

Revision ID: d1e2f3a4b5c6
Revises: c9d0e1f2a3b4
Create Date: 2026-07-29 22:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, Sequence[str], None] = "c9d0e1f2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Constraint may be named either by SQLAlchemy or by raw schema.sql
    op.execute("ALTER TABLE customers DROP CONSTRAINT IF EXISTS check_loyalty_status")
    op.execute("ALTER TABLE customers DROP CONSTRAINT IF EXISTS customers_loyalty_status_check")
    op.drop_column("customers", "loyalty_status")


def downgrade() -> None:
    op.add_column(
        "customers",
        sa.Column(
            "loyalty_status",
            sa.String(length=20),
            nullable=False,
            server_default="bronze",
        ),
    )
    op.create_check_constraint(
        "check_loyalty_status",
        "customers",
        "loyalty_status IN ('bronze','silver','gold','platinum')",
    )
