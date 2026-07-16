"""add invitation lifecycle metadata

Revision ID: c5f8a2d6e310
Revises: d6d2768c3e76
"""

import sqlalchemy as sa
from alembic import op

revision = "c5f8a2d6e310"
down_revision = "d6d2768c3e76"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "workspace_invites",
        sa.Column("status", sa.Text(), server_default="pending", nullable=False),
    )
    op.add_column("workspace_invites", sa.Column("invited_by_user_id", sa.UUID(), nullable=True))
    op.add_column(
        "workspace_invites", sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "workspace_invites", sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "workspace_invites",
        sa.Column("resend_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "workspace_invites",
        sa.Column(
            "last_sent_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.execute(
        "UPDATE workspace_invites SET invited_by_user_id = workspaces.owner_id "
        "FROM workspaces WHERE workspace_invites.workspace_id = workspaces.id"
    )
    op.alter_column("workspace_invites", "invited_by_user_id", nullable=False)
    op.create_foreign_key(
        "fk_workspace_invites_invited_by_user_id",
        "workspace_invites",
        "app_users",
        ["invited_by_user_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_workspace_invites_invited_by_user_id", "workspace_invites", type_="foreignkey"
    )
    for column in (
        "last_sent_at",
        "resend_count",
        "revoked_at",
        "accepted_at",
        "invited_by_user_id",
        "status",
    ):
        op.drop_column("workspace_invites", column)
