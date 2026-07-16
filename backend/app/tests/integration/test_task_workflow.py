import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.background_job import BackgroundJob
from app.worker import process_background_job


@pytest.mark.anyio
async def test_task_crud_and_due_reminder(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_headers: dict,
):
    workspace_response = await client.post(
        "/api/v1/workspaces",
        json={"name": "Task Workflow"},
        headers=mock_headers,
    )
    workspace_id = workspace_response.json()["id"]
    member_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/members/me",
        headers=mock_headers,
    )
    member_user_id = member_response.json()["user_id"]

    person_response = await client.post(
        f"/api/v1/people?workspace_id={workspace_id}",
        json={
            "name": "Task Person",
            "linkedin_url": "https://linkedin.com/in/task-person",
        },
        headers=mock_headers,
    )
    person_id = person_response.json()["id"]
    due_date = date.today() - timedelta(days=1)

    create_response = await client.post(
        f"/api/v1/tasks?workspace_id={workspace_id}",
        json={
            "person_id": person_id,
            "title": "Send proposal",
            "description": "Include pricing",
            "due_date": str(due_date),
            "assigned_to": member_user_id,
        },
        headers=mock_headers,
    )
    assert create_response.status_code == 201
    task = create_response.json()
    assert task["person_name"] == "Task Person"
    assert task["assignee_email"] == "test@example.com"

    list_response = await client.get(
        f"/api/v1/tasks?workspace_id={workspace_id}&assigned_to={member_user_id}&status=open",
        headers=mock_headers,
    )
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    job = (
        (
            await db_session.execute(
                select(BackgroundJob).where(
                    BackgroundJob.workspace_id == uuid.UUID(workspace_id),
                    BackgroundJob.job_type == "daily_digest",
                )
            )
        )
        .scalars()
        .first()
    )
    assert job is not None
    await process_background_job(db_session, job)

    notifications_response = await client.get(
        f"/api/v1/notifications?workspace_id={workspace_id}",
        headers=mock_headers,
    )
    reminders = [
        item
        for item in notifications_response.json()
        if item["notification_type"] == "task_reminder"
    ]
    assert len(reminders) == 1
    assert reminders[0]["person_id"] == person_id

    complete_response = await client.patch(
        f"/api/v1/tasks/{task['id']}?workspace_id={workspace_id}",
        json={"status": "completed"},
        headers=mock_headers,
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["completed_at"] is not None
