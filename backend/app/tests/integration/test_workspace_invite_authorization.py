import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace_invite import WorkspaceInvite


@pytest.mark.anyio
async def test_only_owner_can_manage_workspace_invites(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_headers: dict,
):
    workspace_response = await client.post(
        "/api/v1/workspaces",
        json={"name": "Invitation Authorization"},
        headers=mock_headers,
    )
    assert workspace_response.status_code == 201
    workspace_id = workspace_response.json()["id"]
    workspace_uuid = uuid.UUID(workspace_id)

    member_headers = {"Authorization": "Bearer member:member@example.com"}
    invite_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invites",
        json={"email": "member@example.com", "role": "member"},
        headers=mock_headers,
    )
    assert invite_response.status_code == 201

    invite = (
        await db_session.execute(
            select(WorkspaceInvite).where(WorkspaceInvite.workspace_id == workspace_uuid)
        )
    ).scalar_one()
    accept_response = await client.post(
        "/api/v1/invites/accept",
        json={"token": invite.token},
        headers=member_headers,
    )
    assert accept_response.status_code == 200

    pending_invite = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invites",
        json={"email": "pending@example.com", "role": "member"},
        headers=mock_headers,
    )
    assert pending_invite.status_code == 201
    pending_invite_id = pending_invite.json()["id"]

    member_requests = (
        ("post", f"/api/v1/workspaces/{workspace_id}/invites", {"email": "blocked@example.com"}),
        ("get", f"/api/v1/workspaces/{workspace_id}/invites", None),
        ("delete", f"/api/v1/workspaces/{workspace_id}/invites/{pending_invite_id}", None),
    )
    for method, path, body in member_requests:
        response = await client.request(method, path, json=body, headers=member_headers)
        assert response.status_code == 403, (method, path)

    outsider_headers = {"Authorization": "Bearer outsider:outsider@example.com"}
    outsider_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/invites",
        headers=outsider_headers,
    )
    assert outsider_response.status_code == 403

    owner_list_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/invites",
        headers=mock_headers,
    )
    assert owner_list_response.status_code == 200
    assert [item["id"] for item in owner_list_response.json()] == [pending_invite_id]
