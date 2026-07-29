"""add promotion media_type + media_filename for local uploads

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-07-29 22:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e2f3a4b5c6d7"
down_revision: Union[str, Sequence[str], None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("promotions", sa.Column("media_type", sa.String(length=20), nullable=True))
    op.add_column("promotions", sa.Column("media_filename", sa.String(length=255), nullable=True))
    op.create_check_constraint(
        "check_promotion_media_type",
        "promotions",
        "media_type IS NULL OR media_type IN ('photo','video')",
    )


def downgrade() -> None:
    op.drop_constraint("check_promotion_media_type", "promotions", type_="check")
    op.drop_column("promotions", "media_filename")
    op.drop_column("promotions", "media_type")
