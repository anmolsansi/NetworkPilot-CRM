"""add structured activity notes

Revision ID: a18f6c9d2e40
Revises: d6d2768c3e76
Create Date: 2026-07-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a18f6c9d2e40"
down_revision: str | None = "d6d2768c3e76"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("activities", sa.Column("interaction_summary", sa.Text(), nullable=True))
    op.add_column("activities", sa.Column("outcome", sa.Text(), nullable=True))
    op.add_column("activities", sa.Column("next_steps", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("activities", "next_steps")
    op.drop_column("activities", "outcome")
    op.drop_column("activities", "interaction_summary")
