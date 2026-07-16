"""add relationship health indicators

Revision ID: a4c9e2f1b807
Revises: d6d2768c3e76
"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a4c9e2f1b807"
down_revision: str | None = "d6d2768c3e76"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "people",
        sa.Column("engagement_score", sa.BigInteger(), server_default="0", nullable=False),
    )
    op.add_column(
        "people",
        sa.Column(
            "relationship_health",
            sa.String(length=32),
            server_default="cold",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("people", "relationship_health")
    op.drop_column("people", "engagement_score")
