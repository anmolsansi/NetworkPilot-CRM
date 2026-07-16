"""Merge parallel feature migration heads.

Revision ID: e4b7c9d1a203
Revises: a4c9e2f1b807, b8e3d7a4c219, a18f6c9d2e40, c5f8a2d6e310
Create Date: 2026-07-16
"""

from collections.abc import Sequence

revision: str = "e4b7c9d1a203"
down_revision: tuple[str, str, str, str] = (
    "a4c9e2f1b807",
    "b8e3d7a4c219",
    "a18f6c9d2e40",
    "c5f8a2d6e310",
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Join the parallel migration branches without changing the schema."""


def downgrade() -> None:
    """Split the merged migration history without changing the schema."""
