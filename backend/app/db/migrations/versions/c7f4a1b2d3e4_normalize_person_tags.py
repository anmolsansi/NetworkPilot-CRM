"""Normalize legacy people tags into tag relationships.

Revision ID: c7f4a1b2d3e4
Revises: 6bfc5792fd2d
Create Date: 2026-07-13 13:35:00
"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c7f4a1b2d3e4"
down_revision: Union[str, None] = "6bfc5792fd2d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    people = bind.execute(
        sa.text("SELECT id, workspace_id, tags FROM people WHERE tags IS NOT NULL")
    ).mappings()

    for person in people:
        names: list[str] = []
        for raw_name in person["tags"] or []:
            name = raw_name.strip()
            if name and name not in names:
                names.append(name)

        for name in names:
            tag_id = bind.execute(
                sa.text("SELECT id FROM tags WHERE workspace_id = :workspace_id AND name = :name"),
                {"workspace_id": person["workspace_id"], "name": name},
            ).scalar_one_or_none()
            if tag_id is None:
                tag_id = uuid.uuid4()
                bind.execute(
                    sa.text("INSERT INTO tags (id, workspace_id, name, color) VALUES (:id, :workspace_id, :name, NULL)"),
                    {"id": tag_id, "workspace_id": person["workspace_id"], "name": name},
                )
            bind.execute(
                sa.text("INSERT INTO person_tags (person_id, tag_id) VALUES (:person_id, :tag_id) ON CONFLICT DO NOTHING"),
                {"person_id": person["id"], "tag_id": tag_id},
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
