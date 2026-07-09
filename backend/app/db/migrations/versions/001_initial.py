"""Initial migration - create all V1 tables

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
import logging
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # app_users
    op.create_table(
        "app_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("supabase_user_id", postgresql.UUID(as_uuid=True), unique=True, nullable=False, index=True),
        sa.Column("email", sa.Text, nullable=False),
        sa.Column("display_name", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # workspaces
    op.create_table(
        "workspaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("app_users.id"), nullable=False, index=True),
        sa.Column("default_follow_up_delay_days", sa.Integer, nullable=False, server_default="3"),
        sa.Column("default_acceptance_check_delay_days", sa.Integer, nullable=False, server_default="1"),
        sa.Column("daily_reminder_time", sa.Time, nullable=False, server_default=sa.text("'09:00:00'")),
        sa.Column("timezone", sa.Text, nullable=False, server_default="'UTC'"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # workspace_members
    op.create_table(
        "workspace_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False, index=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("app_users.id"), nullable=False, index=True),
        sa.Column("role", sa.Text, nullable=False, server_default="'member'"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_workspace_members_workspace_user",
        "workspace_members",
        ["workspace_id", "user_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # people
    op.create_table(
        "people",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False, index=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("linkedin_url", sa.Text, nullable=False),
        sa.Column("linkedin_slug", sa.Text, nullable=False, index=True),
        sa.Column("role", sa.Text, nullable=True),
        sa.Column("company", sa.Text, nullable=True),
        sa.Column("location", sa.Text, nullable=True),
        sa.Column("priority", sa.String(1), nullable=False, server_default="'B'"),
        sa.Column("stage", sa.Text, nullable=False, server_default="'invite_sent'"),
        sa.Column("status", sa.Text, nullable=False, server_default="'active'"),
        sa.Column("next_action_type", sa.Text, nullable=True),
        sa.Column("next_action_date", sa.Date, nullable=True),
        sa.Column("last_action_type", sa.Text, nullable=True),
        sa.Column("last_action_date", sa.Date, nullable=True),
        sa.Column("connection_note", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.Text), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_people_stage", "people", ["stage"])
    op.create_index("ix_people_status", "people", ["status"])
    op.create_index("ix_people_priority", "people", ["priority"])
    op.create_index("ix_people_next_action_date", "people", ["next_action_date"])
    op.create_index(
        "ix_people_workspace_url",
        "people",
        ["workspace_id", "linkedin_url"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # activities
    op.create_table(
        "activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people.id"), nullable=False, index=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False, index=True),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("app_users.id"), nullable=False),
        sa.Column("action_type", sa.Text, nullable=False),
        sa.Column("source", sa.Text, nullable=False),
        sa.Column("previous_stage", sa.Text, nullable=True),
        sa.Column("new_stage", sa.Text, nullable=True),
        sa.Column("message", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_activities_created_at", "activities", ["created_at"])

    # message_templates
    op.create_table(
        "message_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False, index=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("category", sa.Text, nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("variables", postgresql.ARRAY(sa.Text), nullable=True),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_message_templates_workspace_name",
        "message_templates",
        ["workspace_id", "name"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # user_settings
    op.create_table(
        "user_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("app_users.id"), unique=True, nullable=False),
        sa.Column("default_workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=True),
        sa.Column("settings_json", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("user_settings")
    op.drop_table("message_templates")
    op.drop_table("activities")
    op.drop_table("people")
    op.drop_table("workspace_members")
    op.drop_table("workspaces")
    op.drop_table("app_users")
