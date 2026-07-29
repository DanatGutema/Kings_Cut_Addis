"""add barbers table and preferred_barber_id on appointments

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-07-28 21:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "barbers",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("first_name", sa.String(length=255), nullable=False),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.Column("phone_number", sa.String(length=15), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("specialty", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone_number"),
        sa.UniqueConstraint("email"),
    )
    op.add_column("appointments", sa.Column("preferred_barber_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_appointments_preferred_barber_id",
        "appointments",
        "barbers",
        ["preferred_barber_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_appointments_preferred_barber_id", "appointments", type_="foreignkey")
    op.drop_column("appointments", "preferred_barber_id")
    op.drop_table("barbers")
