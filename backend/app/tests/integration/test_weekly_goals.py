import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.activity import Activity
from app.models.workspace import Workspace


@pytest.mark.anyio
async def test_configurable_weekly_goals_count_workspace_metrics(
    client: AsyncClient, mock_headers: dict, db_session
):
    workspace_response = await client.post(
        "/api/v1/workspaces",
        json={"name": "Goals", "timezone": "Asia/Kolkata"},
        headers=mock_headers,
    )
    workspace_id = workspace_response.json()["id"]
    workspace = await db_session.scalar(
        select(Workspace).where(Workspace.id == uuid.UUID(workspace_id))
    )
    person_response = await client.post(
        f"/api/v1/people?workspace_id={workspace_id}",
        json={"name": "Goal Person", "linkedin_url": f"https://linkedin.com/in/{uuid.uuid4()}"},
        headers=mock_headers,
    )
    person_id = uuid.UUID(person_response.json()["id"])
    now = datetime.now(timezone.utc)
    db_session.add_all(
        [
            Activity(
                person_id=person_id,
                workspace_id=uuid.UUID(workspace_id),
                actor_user_id=workspace.owner_id,
                action_type=action,
                source="web_app",
                previous_stage="accepted",
                new_stage="accepted",
                created_at=now,
            )
            for action in ("invite_sent", "follow_up_1_sent", "reply_received")
        ]
    )
    await db_session.flush()
    configured = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/members/me",
        json={
            "weekly_goals": {
                "profiles_added": 2,
                "invitations_sent": 4,
                "follow_ups_sent": 5,
                "replies_received": 2,
            }
        },
        headers=mock_headers,
    )
    assert configured.status_code == 200

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/analytics/goals", headers=mock_headers
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["timezone"] == "Asia/Kolkata"
    assert data["period_start"].endswith("Z")
    assert data["period_end"].endswith("Z")
    metrics = {item["metric"]: item for item in data["metrics"]}
    assert metrics["profiles_added"] == {
        "metric": "profiles_added",
        "label": "Profiles added",
        "target": 2,
        "current": 1,
        "percentage": 50.0,
    }
    assert metrics["invitations_sent"]["current"] == 1
    assert metrics["follow_ups_sent"]["current"] == 1
    assert metrics["replies_received"]["current"] == 1
