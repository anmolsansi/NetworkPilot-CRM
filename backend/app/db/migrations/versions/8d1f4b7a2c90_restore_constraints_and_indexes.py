"""Restore dropped indexes and add configuration constraints.

Revision ID: 8d1f4b7a2c90
Revises: 7a9c2f1d4e60
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "8d1f4b7a2c90"
down_revision: str | None = "7a9c2f1d4e60"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "pipeline_stages",
        sa.Column(
            "allowed_next_stage_ids",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.create_unique_constraint(
        "uq_saved_view_user_name", "saved_people_views", ["workspace_id", "user_id", "name"]
    )
    op.create_unique_constraint(
        "uq_custom_field_workspace_name", "custom_fields", ["workspace_id", "name"]
    )
    op.create_unique_constraint(
        "uq_pipeline_stage_workspace_name", "pipeline_stages", ["workspace_id", "name"]
    )
    op.create_unique_constraint(
        "uq_pipeline_stage_workspace_order", "pipeline_stages", ["workspace_id", "order"]
    )

    op.execute("CREATE INDEX IF NOT EXISTS ix_activities_created_at ON activities (created_at)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_import_batches_workspace_created "
        "ON import_batches (workspace_id, created_at)"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_message_templates_workspace_name "
        "ON message_templates (workspace_id, name) WHERE deleted_at IS NULL"
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_people_next_action_date ON people (next_action_date)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_people_priority ON people (priority)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_people_stage ON people (stage)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_people_status ON people (status)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_people_workspace_favorite "
        "ON people (workspace_id, is_favorite)"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_people_workspace_url "
        "ON people (workspace_id, linkedin_url) WHERE deleted_at IS NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_workspace_members_workspace_user "
        "ON workspace_members (workspace_id, user_id) WHERE deleted_at IS NULL"
    )


def downgrade() -> None:
    op.drop_index("ix_workspace_members_workspace_user", table_name="workspace_members")
    op.drop_index("ix_people_workspace_url", table_name="people")
    op.drop_index("ix_people_workspace_favorite", table_name="people")
    op.drop_index("ix_people_status", table_name="people")
    op.drop_index("ix_people_stage", table_name="people")
    op.drop_index("ix_people_priority", table_name="people")
    op.drop_index("ix_people_next_action_date", table_name="people")
    op.drop_index("ix_message_templates_workspace_name", table_name="message_templates")
    op.drop_index("ix_import_batches_workspace_created", table_name="import_batches")
    op.drop_index("ix_activities_created_at", table_name="activities")
    op.drop_constraint("uq_pipeline_stage_workspace_order", "pipeline_stages", type_="unique")
    op.drop_constraint("uq_pipeline_stage_workspace_name", "pipeline_stages", type_="unique")
    op.drop_constraint("uq_custom_field_workspace_name", "custom_fields", type_="unique")
    op.drop_constraint("uq_saved_view_user_name", "saved_people_views", type_="unique")
    op.drop_column("pipeline_stages", "allowed_next_stage_ids")
