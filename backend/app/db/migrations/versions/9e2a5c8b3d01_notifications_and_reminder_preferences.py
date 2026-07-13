"""Add notification centre and reminder preferences.

Revision ID: 9e2a5c8b3d01
Revises: 8d1f4b7a2c90
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "9e2a5c8b3d01"
down_revision: str | None = "8d1f4b7a2c90"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("workspaces", sa.Column("quiet_hours_start", sa.Time(), nullable=True))
    op.add_column("workspaces", sa.Column("quiet_hours_end", sa.Time(), nullable=True))
    op.add_column(
        "workspaces",
        sa.Column("email_reminders_enabled", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.add_column(
        "workspaces",
        sa.Column("daily_digest_enabled", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.add_column(
        "workspaces",
        sa.Column("overdue_alerts_enabled", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notification_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["app_users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["person_id"], ["people.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_workspace_id", "notifications", ["workspace_id"])
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_index("ix_notifications_workspace_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_column("workspaces", "overdue_alerts_enabled")
    op.drop_column("workspaces", "daily_digest_enabled")
    op.drop_column("workspaces", "email_reminders_enabled")
    op.drop_column("workspaces", "quiet_hours_end")
    op.drop_column("workspaces", "quiet_hours_start")
