"""Normalize legacy people tags into tag relationships.

Revision ID: c7f4a1b2d3e4
Revises: 6bfc5792fd2d
Create Date: 2026-07-13 13:35:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c7f4a1b2d3e4"
down_revision: Union[str, None] = "6bfc5792fd2d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Keep this data migration set-based so it works both against a live database
    # and when a managed deployment generates the full migration chain as SQL.
    op.execute(
        """
        WITH normalized AS (
            SELECT DISTINCT p.workspace_id, btrim(raw.name) AS name
            FROM people AS p
            CROSS JOIN LATERAL unnest(p.tags) AS raw(name)
            WHERE p.tags IS NOT NULL AND btrim(raw.name) <> ''
        )
        INSERT INTO tags (id, workspace_id, name, color)
        SELECT md5(n.workspace_id::text || ':' || n.name)::uuid,
               n.workspace_id,
               n.name,
               NULL
        FROM normalized AS n
        ON CONFLICT (workspace_id, name) DO NOTHING
        """
    )
    op.execute(
        """
        WITH normalized AS (
            SELECT DISTINCT p.id AS person_id,
                            p.workspace_id,
                            btrim(raw.name) AS name
            FROM people AS p
            CROSS JOIN LATERAL unnest(p.tags) AS raw(name)
            WHERE p.tags IS NOT NULL AND btrim(raw.name) <> ''
        )
        INSERT INTO person_tags (person_id, tag_id)
        SELECT n.person_id, t.id
        FROM normalized AS n
        JOIN tags AS t
          ON t.workspace_id = n.workspace_id AND t.name = n.name
        ON CONFLICT DO NOTHING
        """
    )

    op.drop_column("people", "tags")


def downgrade() -> None:
    op.add_column("people", sa.Column("tags", postgresql.ARRAY(sa.Text()), nullable=True))
    op.get_bind().execute(
        sa.text(
            """
            UPDATE people AS p
            SET tags = values_by_person.names
            FROM (
                SELECT pt.person_id, array_agg(t.name ORDER BY t.name) AS names
                FROM person_tags AS pt
                JOIN tags AS t ON t.id = pt.tag_id
                GROUP BY pt.person_id
            ) AS values_by_person
            WHERE p.id = values_by_person.person_id
            """
        )
    )
