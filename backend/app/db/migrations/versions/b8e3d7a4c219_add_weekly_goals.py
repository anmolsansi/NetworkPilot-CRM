"""add configurable weekly goals

Revision ID: b8e3d7a4c219
Revises: d6d2768c3e76
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "b8e3d7a4c219"
down_revision = "d6d2768c3e76"
branch_labels = None
depends_on = None

DEFAULT_GOALS = (
    '{"profiles_added":25,"invitations_sent":50,"follow_ups_sent":25,"replies_received":10}'
)


def upgrade() -> None:
    op.add_column(
        "workspace_members",
        sa.Column(
            "weekly_goals",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=DEFAULT_GOALS,
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("workspace_members", "weekly_goals")
