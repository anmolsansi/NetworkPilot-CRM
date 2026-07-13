"""Harden durable CSV import jobs.

Revision ID: 7a9c2f1d4e60
Revises: 5b75d7b78b6c
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "7a9c2f1d4e60"
down_revision: str | None = "5b75d7b78b6c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("import_jobs", sa.Column("file_name", sa.String(255), nullable=True))
    op.add_column(
        "import_jobs",
        sa.Column(
            "default_initial_action_type",
            sa.String(50),
            nullable=False,
            server_default="invite_sent",
        ),
    )
    op.add_column(
        "import_jobs",
        sa.Column("duplicate_strategy", sa.String(20), nullable=False, server_default="skip"),
    )
    op.add_column(
        "import_jobs",
        sa.Column("default_priority", sa.String(1), nullable=False, server_default="B"),
    )
    op.add_column(
        "import_jobs", sa.Column("failed_rows", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column(
        "import_jobs", sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column("import_jobs", sa.Column("started_at", sa.DateTime(), nullable=True))
    op.add_column("import_jobs", sa.Column("heartbeat_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("import_jobs", "heartbeat_at")
    op.drop_column("import_jobs", "started_at")
    op.drop_column("import_jobs", "attempt_count")
    op.drop_column("import_jobs", "failed_rows")
    op.drop_column("import_jobs", "default_priority")
    op.drop_column("import_jobs", "duplicate_strategy")
    op.drop_column("import_jobs", "default_initial_action_type")
    op.drop_column("import_jobs", "file_name")
