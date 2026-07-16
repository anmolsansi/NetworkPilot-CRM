import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.activity import Activity
from app.models.import_job import ImportJob
from app.models.person import Person
from app.models.task import Task
from app.models.workspace import Workspace


@pytest.mark.anyio
async def test_dashboard_widgets_are_populated_and_workspace_scoped(
    client: AsyncClient,
    mock_headers: dict,
    db_session,
):
    workspace_response = await client.post(
        "/api/v1/workspaces", json={"name": "Widgets"}, headers=mock_headers
    )
    workspace_id = workspace_response.json()["id"]
    workspace = await db_session.scalar(
        select(Workspace).where(Workspace.id == uuid.UUID(workspace_id))
    )
    person_response = await client.post(
        f"/api/v1/people?workspace_id={workspace_id}",
        json={
            "name": "Widget Person",
            "linkedin_url": f"https://linkedin.com/in/{uuid.uuid4()}",
            "is_favorite": True,
        },
        headers=mock_headers,
    )
    person_id = uuid.UUID(person_response.json()["id"])
    person = await db_session.scalar(select(Person).where(Person.id == person_id))
    person.last_action_date = date.today() - timedelta(days=45)
    accepted_at = datetime.now(timezone.utc) - timedelta(days=2)
    db_session.add_all(
        [
            Activity(
                person_id=person_id,
                workspace_id=uuid.UUID(workspace_id),
                actor_user_id=workspace.owner_id,
                action_type="accepted",
                source="web_app",
                previous_stage="invite_pending",
                new_stage="accepted",
                created_at=accepted_at,
            ),
            Task(
                workspace_id=uuid.UUID(workspace_id),
                person_id=person_id,
                title="Overdue follow-up",
                due_date=date.today() - timedelta(days=1),
                status="open",
            ),
            ImportJob(
                workspace_id=uuid.UUID(workspace_id),
                created_by_user_id=workspace.owner_id,
                file_content="Name,LinkedIn URL\nTest,https://linkedin.com/in/test",
                file_name="contacts.csv",
                status="completed",
                total_rows=1,
                failed_rows=0,
            ),
        ]
    )
    await db_session.flush()

    response = await client.get(
        f"/api/v1/dashboard/widgets?workspace_id={workspace_id}",
        headers=mock_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert [item["name"] for item in data["favourites"]] == ["Widget Person"]
    assert [item["name"] for item in data["newly_accepted"]] == ["Widget Person"]
    assert [item["name"] for item in data["stale_relationships"]] == ["Widget Person"]
    assert data["overdue_tasks"][0]["title"] == "Overdue follow-up"
    assert data["recent_imports"][0]["file_name"] == "contacts.csv"


@pytest.mark.anyio
async def test_dashboard_config_is_versioned_validated_and_ordered(
    client: AsyncClient,
    mock_headers: dict,
):
    workspace = await client.post(
        "/api/v1/workspaces", json={"name": "Widget config"}, headers=mock_headers
    )
    workspace_id = workspace.json()["id"]
    response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/members/me",
        json={
            "dashboard_config": {
                "version": 1,
                "widgets": [
                    {"id": "recent_imports", "visible": True, "limit": 3},
                    {"id": "favourites", "visible": False, "limit": 7},
                ],
            }
        },
        headers=mock_headers,
    )
    assert response.status_code == 200, response.text
    config = response.json()["dashboard_config"]
    assert config["version"] == 1
    assert [widget["id"] for widget in config["widgets"][:2]] == [
        "recent_imports",
        "favourites",
    ]
    assert len(config["widgets"]) == 8
    assert config["widgets"][0]["limit"] == 3

    invalid = await client.patch(
        f"/api/v1/workspaces/{workspace_id}/members/me",
        json={
            "dashboard_config": {
                "version": 1,
                "widgets": [
                    {"id": "summary", "limit": 5},
                    {"id": "summary", "limit": 5},
                ],
            }
        },
        headers=mock_headers,
    )
    assert invalid.status_code == 422
