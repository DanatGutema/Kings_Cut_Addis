"""staff email nullable + approval_status for self-registration

Revision ID: c9d0e1f2a3b4
Revises: b7c8d9e0f1a2
Create Date: 2026-07-28 21:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, Sequence[str], None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "staff",
        sa.Column(
            "approval_status",
            sa.String(length=20),
            nullable=False,
            server_default="approved",
        ),
    )
    op.create_check_constraint(
        "check_staff_approval_status",
        "staff",
        "approval_status IN ('pending','approved','rejected')",
    )
    op.alter_column("staff", "email", existing_type=sa.String(length=255), nullable=True)


def downgrade() -> None:
    op.execute("UPDATE staff SET email = 'unknown-' || id::text || '@placeholder.local' WHERE email IS NULL")
    op.alter_column("staff", "email", existing_type=sa.String(length=255), nullable=False)
    op.drop_constraint("check_staff_approval_status", "staff", type_="check")
    op.drop_column("staff", "approval_status")
