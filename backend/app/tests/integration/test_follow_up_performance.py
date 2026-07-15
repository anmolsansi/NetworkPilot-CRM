import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.activity import Activity
from app.models.template import MessageTemplate
from app.models.workspace import Workspace


@pytest.mark.anyio
async def test_follow_up_performance_dimensions_periods_and_reply_attribution(
    client: AsyncClient,
    mock_headers: dict,
    db_session,
):
    workspace_response = await client.post(
        "/api/v1/workspaces", json={"name": "Performance"}, headers=mock_headers
    )
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]
    workspace = await db_session.scalar(
        select(Workspace).where(Workspace.id == uuid.UUID(workspace_id))
    )

    people = []
    for index, (company, role) in enumerate([("Acme", "Engineer"), ("Beta", "Manager")]):
        response = await client.post(
            f"/api/v1/people?workspace_id={workspace_id}",
            json={
                "name": f"Performance Person {index}",
                "linkedin_url": f"https://linkedin.com/in/{uuid.uuid4()}",
                "company": company,
                "role": role,
            },
            headers=mock_headers,
        )
        assert response.status_code == 201
        people.append(response.json())

    templates = [
        MessageTemplate(
            workspace_id=uuid.UUID(workspace_id),
            name=name,
            category="follow_up",
            body="Hello",
            variables=[],
        )
        for name in ("Template A", "Template B")
    ]
    db_session.add_all(templates)
    await db_session.flush()

    def activity(person_index, action_type, created_at, template_index=None, stage="accepted"):
        return Activity(
            person_id=uuid.UUID(people[person_index]["id"]),
            workspace_id=uuid.UUID(workspace_id),
            actor_user_id=workspace.owner_id,
            action_type=action_type,
            source="web_app",
            previous_stage=stage,
            new_stage="waiting_for_reply" if action_type != "reply_received" else "replied",
            template_id=templates[template_index].id if template_index is not None else None,
            created_at=created_at,
        )

    db_session.add_all(
        [
            activity(0, "message_sent", datetime(2026, 1, 1, tzinfo=timezone.utc), 0),
            activity(0, "follow_up_1_sent", datetime(2026, 1, 10, tzinfo=timezone.utc), 1),
            activity(0, "reply_received", datetime(2026, 1, 11, tzinfo=timezone.utc)),
            activity(1, "message_sent", datetime(2026, 2, 1, tzinfo=timezone.utc), 0),
            activity(1, "reply_received", datetime(2026, 2, 5, tzinfo=timezone.utc)),
        ]
    )
    await db_session.flush()

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/analytics/performance",
        headers=mock_headers,
    )
    assert response.status_code == 200
    by_label = {row["dimension_label"]: row for row in response.json()}
    assert by_label["Template A"]["sent_count"] == 2
    assert by_label["Template A"]["reply_count"] == 1
    assert by_label["Template A"]["reply_rate"] == 50.0
    assert by_label["Template B"]["sent_count"] == 1
    assert by_label["Template B"]["reply_count"] == 1

    january = await client.get(
        f"/api/v1/workspaces/{workspace_id}/analytics/performance",
        params={"date_from": "2026-01-01", "date_to": "2026-01-31"},
        headers=mock_headers,
    )
    january_rows = {row["dimension_label"]: row for row in january.json()}
    assert january_rows["Template A"]["reply_count"] == 0
    assert january_rows["Template B"]["reply_count"] == 1

    for dimension, expected_labels in (
        ("company", {"Acme", "Beta"}),
        ("position", {"Engineer", "Manager"}),
        ("stage", {"Accepted"}),
        ("week", {"2025-12-29", "2026-01-05", "2026-01-26"}),
    ):
        grouped = await client.get(
            f"/api/v1/workspaces/{workspace_id}/analytics/performance",
            params={"group_by": dimension},
            headers=mock_headers,
        )
        assert grouped.status_code == 200
        assert {row["dimension_label"] for row in grouped.json()} == expected_labels
