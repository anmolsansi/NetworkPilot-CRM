"""Add import batch audit history

Revision ID: 002_import_batches
Revises: 001_initial
Create Date: 2026-07-03 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_import_batches"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "import_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("app_users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("file_name", sa.Text, nullable=True),
        sa.Column("total_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("valid_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("duplicate_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("invalid_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.Text, nullable=False, server_default="'previewed'"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_import_batches_workspace_created",
        "import_batches",
        ["workspace_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_import_batches_workspace_created", table_name="import_batches")
    op.drop_table("import_batches")
