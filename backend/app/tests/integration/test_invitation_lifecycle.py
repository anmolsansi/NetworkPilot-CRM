import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.workspace_invite import WorkspaceInvite


@pytest.mark.anyio
async def test_invitation_create_resend_expire_wrong_email_accept_and_revoke(
    client: AsyncClient, mock_headers: dict, db_session
):
    workspace = await client.post(
        "/api/v1/workspaces", json={"name": "Invitations"}, headers=mock_headers
    )
    workspace_id = workspace.json()["id"]
    invalid_role = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invites",
        json={"email": "admin@example.com", "role": "admin"},
        headers=mock_headers,
    )
    assert invalid_role.status_code == 422

    created = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invites",
        json={"email": "recipient@example.com", "role": "member"},
        headers=mock_headers,
    )
    assert created.status_code == 201, created.text
    assert created.json()["status"] == "pending"
    invite_id = created.json()["id"]
    invite = await db_session.scalar(
        select(WorkspaceInvite).where(WorkspaceInvite.id == uuid.UUID(invite_id))
    )
    first_token = invite.token

    resent = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invites/{invite_id}/resend",
        headers=mock_headers,
    )
    assert resent.status_code == 200
    assert resent.json()["resend_count"] == 1
    await db_session.refresh(invite)
    assert invite.token != first_token

    wrong = await client.post(
        "/api/v1/invites/accept",
        json={"token": invite.token},
        headers={"Authorization": "Bearer other:other@example.com"},
    )
    assert wrong.status_code == 422

    accepted = await client.post(
        "/api/v1/invites/accept",
        json={"token": invite.token},
        headers={"Authorization": "Bearer recipient:recipient@example.com"},
    )
    assert accepted.status_code == 200, accepted.text
    await db_session.refresh(invite)
    assert invite.status == "accepted"
    assert invite.accepted_at is not None

    expired_create = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invites",
        json={"email": "expired@example.com"},
        headers=mock_headers,
    )
    expired = await db_session.scalar(
        select(WorkspaceInvite).where(WorkspaceInvite.id == uuid.UUID(expired_create.json()["id"]))
    )
    expired.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    await db_session.flush()
    listed = await client.get(f"/api/v1/workspaces/{workspace_id}/invites", headers=mock_headers)
    assert (
        next(item for item in listed.json() if item["id"] == str(expired.id))["status"] == "expired"
    )
    revoked = await client.delete(
        f"/api/v1/workspaces/{workspace_id}/invites/{expired.id}", headers=mock_headers
    )
    assert revoked.status_code == 204
    await db_session.refresh(expired)
    assert expired.status == "revoked"
    assert expired.revoked_at is not None
