import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace_invite import WorkspaceInvite


@pytest.mark.anyio
async def test_member_directory_and_bulk_contact_ownership(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_headers: dict,
):
    workspace_response = await client.post(
        "/api/v1/workspaces",
        json={"name": "Contact Ownership"},
        headers=mock_headers,
    )
    workspace_id = workspace_response.json()["id"]
    workspace_uuid = uuid.UUID(workspace_id)

    invite_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invites",
        json={"email": "owner-member@example.com", "role": "member"},
        headers=mock_headers,
    )
    assert invite_response.status_code == 201
    invite = (
        await db_session.execute(
            select(WorkspaceInvite).where(WorkspaceInvite.workspace_id == workspace_uuid)
        )
    ).scalar_one()
    member_headers = {
        "Authorization": "Bearer owner-member:owner-member@example.com"
    }
    accept_response = await client.post(
        "/api/v1/invites/accept",
        json={"token": invite.token},
        headers=member_headers,
    )
    assert accept_response.status_code == 200
    member_user_id = accept_response.json()["user_id"]

    directory_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/members",
        headers=member_headers,
    )
    assert directory_response.status_code == 200
    assert {entry["email"] for entry in directory_response.json()} == {
        "test@example.com",
        "owner-member@example.com",
    }

    person_ids = []
    for index in range(2):
        person_response = await client.post(
            f"/api/v1/people?workspace_id={workspace_id}",
            json={
                "name": f"Owned Person {index}",
                "linkedin_url": f"https://linkedin.com/in/owned-person-{index}",
            },
            headers=mock_headers,
        )
        person_ids.append(person_response.json()["id"])

    assign_response = await client.post(
        "/api/v1/people/bulk-actions",
        json={
            "workspace_id": workspace_id,
            "person_ids": person_ids,
            "action": "set_owner",
            "payload": {"owner_id": member_user_id},
        },
        headers=mock_headers,
    )
    assert assign_response.status_code == 200
    assert {item["owner_id"] for item in assign_response.json()["items"]} == {
        member_user_id
    }

    filtered_response = await client.get(
        f"/api/v1/people?workspace_id={workspace_id}&owner_id={member_user_id}",
        headers=mock_headers,
    )
    assert filtered_response.status_code == 200
    assert filtered_response.json()["total"] == 2

    invalid_owner_response = await client.post(
        "/api/v1/people/bulk-actions",
        json={
            "workspace_id": workspace_id,
            "person_ids": person_ids,
            "action": "set_owner",
            "payload": {"owner_id": str(uuid.uuid4())},
        },
        headers=mock_headers,
    )
    assert invalid_owner_response.status_code == 422

    unassign_response = await client.post(
        "/api/v1/people/bulk-actions",
        json={
            "workspace_id": workspace_id,
            "person_ids": person_ids,
            "action": "set_owner",
            "payload": {"owner_id": None},
        },
        headers=mock_headers,
    )
    assert unassign_response.status_code == 200
    assert all(item["owner_id"] is None for item in unassign_response.json()["items"])
