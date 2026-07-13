"""Add Octopus CRM contact fields to people.

Revision ID: 004_octopus_people_fields
Revises: 003_workspace_members_updated_at
"""

import sqlalchemy as sa
from alembic import op

revision = "004_octopus_people_fields"
down_revision = "003_workspace_members_updated_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("people", sa.Column("first_name", sa.Text(), nullable=True))
    op.add_column("people", sa.Column("last_name", sa.Text(), nullable=True))
    op.add_column("people", sa.Column("email", sa.Text(), nullable=True))
    op.add_column("people", sa.Column("phone_number", sa.Text(), nullable=True))
    op.add_column("people", sa.Column("premium", sa.Boolean(), nullable=True))
    op.add_column("people", sa.Column("company_website", sa.Text(), nullable=True))
    op.add_column("people", sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("people", sa.Column("processed_at_millis", sa.BigInteger(), nullable=True))
    op.add_column(
        "people", sa.Column("invite_accepted_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("people", sa.Column("invite_accepted_at_millis", sa.BigInteger(), nullable=True))


def downgrade() -> None:
    for column in (
        "invite_accepted_at_millis",
        "invite_accepted_at",
        "processed_at_millis",
        "processed_at",
        "company_website",
        "premium",
        "phone_number",
        "email",
        "last_name",
        "first_name",
    ):
        op.drop_column("people", column)
