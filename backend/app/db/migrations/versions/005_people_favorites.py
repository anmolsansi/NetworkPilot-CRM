"""Add favourite fields to people.

Revision ID: 005_people_favorites
Revises: 004_octopus_people_fields
"""

import sqlalchemy as sa
from alembic import op

revision = "005_people_favorites"
down_revision = "004_octopus_people_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "people",
        sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column("people", sa.Column("favorite_notes", sa.Text(), nullable=True))
    op.create_index(
        "ix_people_workspace_favorite",
        "people",
        ["workspace_id", "is_favorite"],
    )


def downgrade() -> None:
    op.drop_index("ix_people_workspace_favorite", table_name="people")
    op.drop_column("people", "favorite_notes")
    op.drop_column("people", "is_favorite")
