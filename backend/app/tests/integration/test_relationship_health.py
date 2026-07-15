import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.background_job import BackgroundJob


@pytest.mark.anyio
async def test_activity_delete_restore_and_manual_warmth_refresh_health(
    client: AsyncClient,
    mock_headers: dict,
):
    workspace_response = await client.post(
        "/api/v1/workspaces",
        json={"name": "Relationship health"},
        headers=mock_headers,
    )
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]
    person_response = await client.post(
        f"/api/v1/people?workspace_id={workspace_id}",
        json={
            "name": "Health Test",
            "linkedin_url": f"https://linkedin.com/in/{uuid.uuid4()}",
        },
        headers=mock_headers,
    )
    assert person_response.status_code == 201
    person_id = person_response.json()["id"]
    assert person_response.json()["relationship_health"] == "cold"
    assert person_response.json()["engagement_score"] == 0

    activity_response = await client.post(
        f"/api/v1/people/{person_id}/activities?workspace_id={workspace_id}",
        json={"action_type": "message_sent", "source": "web_app"},
        headers=mock_headers,
    )
    assert activity_response.status_code == 201
    activity_id = activity_response.json()["id"]

    person = (
        await client.get(
            f"/api/v1/people/{person_id}?workspace_id={workspace_id}",
            headers=mock_headers,
        )
    ).json()
    assert person["calculated_freshness"] == 100
    assert person["engagement_score"] == 64
    assert person["relationship_health"] == "strong"
    assert person["last_engaged_at"] is not None

    deleted = await client.delete(
        f"/api/v1/activities/{activity_id}?workspace_id={workspace_id}",
        headers=mock_headers,
    )
    assert deleted.status_code == 204
    person = (
        await client.get(
            f"/api/v1/people/{person_id}?workspace_id={workspace_id}",
            headers=mock_headers,
        )
    ).json()
    assert person["calculated_freshness"] == 0
    assert person["engagement_score"] == 0
    assert person["relationship_health"] == "cold"
    assert person["last_engaged_at"] is None

    restored = await client.post(
        f"/api/v1/activities/{activity_id}/restore?workspace_id={workspace_id}",
        headers=mock_headers,
    )
    assert restored.status_code == 200
    person = (
        await client.patch(
            f"/api/v1/people/{person_id}?workspace_id={workspace_id}",
            json={"manual_warmth": 1},
            headers=mock_headers,
        )
    ).json()
    assert person["relationship_health"] == "cold"
    assert person["last_engaged_at"] is not None


@pytest.mark.anyio
async def test_workspace_schedules_relationship_health_refresh(
    client: AsyncClient,
    mock_headers: dict,
    db_session,
):
    response = await client.post(
        "/api/v1/workspaces",
        json={"name": "Scheduled relationship refresh"},
        headers=mock_headers,
    )
    assert response.status_code == 201
    workspace_id = uuid.UUID(response.json()["id"])
    job_types = set(
        (
            await db_session.scalars(
                select(BackgroundJob.job_type).where(BackgroundJob.workspace_id == workspace_id)
            )
        ).all()
    )
    assert {"daily_digest", "relationship_health_refresh"} <= job_types
