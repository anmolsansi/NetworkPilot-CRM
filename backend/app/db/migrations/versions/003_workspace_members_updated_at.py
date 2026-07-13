"""Add updated_at to workspace members

Revision ID: 003_workspace_members_updated_at
Revises: 002_import_batches
Create Date: 2026-07-09 17:10:00.000000
"""

import logging
from typing import Sequence, Union

from alembic import op

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)

revision: str = "003_workspace_members_updated_at"
down_revision: Union[str, None] = "002_import_batches"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE workspace_members
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE workspace_members
        DROP COLUMN IF EXISTS updated_at
        """
    )
