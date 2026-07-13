import logging

import pytest
from httpx import AsyncClient

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)


@pytest.mark.anyio
class TestCrossWorkspaceAuthorization:
    async def test_cross_workspace_access_denied(self, client: AsyncClient, mock_headers: dict):
        # Create workspace A for User A
        resp = await client.post(
            "/api/v1/workspaces", json={"name": "Workspace A"}, headers=mock_headers
        )
        assert resp.status_code == 201
        workspace_a_id = resp.json()["id"]

        # User B headers
        user_b_headers = {"Authorization": "Bearer user_b:user_b@example.com"}

        # Create workspace B for User B
        resp = await client.post(
            "/api/v1/workspaces", json={"name": "Workspace B"}, headers=user_b_headers
        )
        assert resp.status_code == 201

        # User B tries to read Workspace A templates
        resp = await client.get(
            f"/api/v1/templates?workspace_id={workspace_a_id}", headers=user_b_headers
        )
        assert resp.status_code == 403

        # User B tries to create template in Workspace A
        resp = await client.post(
            f"/api/v1/templates?workspace_id={workspace_a_id}",
            json={"name": "Hacked", "category": "Test", "body": "Test"},
            headers=user_b_headers,
        )
        assert resp.status_code == 403

        # User B tries to lookup extension profile in Workspace A
        resp = await client.get(
            f"/api/v1/extension/lookup?workspace_id={workspace_a_id}&linkedin_url=test",
            headers=user_b_headers,
        )
        assert resp.status_code == 403

        # User B tries to quick-create in Workspace A
        resp = await client.post(
            "/api/v1/extension/quick-create",
            json={
                "workspace_id": workspace_a_id,
                "name": "Test",
                "linkedin_url": "test",
                "initial_action": "invite_sent",
            },
            headers=user_b_headers,
        )
        assert resp.status_code == 403

        # User B tries to update Workspace A settings
        resp = await client.patch(
            f"/api/v1/workspaces/{workspace_a_id}", json={"name": "Hacked"}, headers=user_b_headers
        )
        assert resp.status_code == 403

        # User A creates a person in Workspace A
        resp = await client.post(
            f"/api/v1/people?workspace_id={workspace_a_id}",
            json={
                "name": "Person A",
                "linkedin_url": "https://linkedin.com/in/a",
                "stage": "identified",
            },
            headers=mock_headers,
        )
        assert resp.status_code == 201
        person_a_id = resp.json()["id"]

        # User B tries to read people in Workspace A
        resp = await client.get(
            f"/api/v1/people?workspace_id={workspace_a_id}", headers=user_b_headers
        )
        assert resp.status_code == 403

        # User B tries to read a specific person in Workspace A
        resp = await client.get(
            f"/api/v1/people/{person_a_id}?workspace_id={workspace_a_id}", headers=user_b_headers
        )
        assert resp.status_code == 403

        # User B tries to create a person in Workspace A
        resp = await client.post(
            f"/api/v1/people?workspace_id={workspace_a_id}",
            json={
                "name": "Person Hacked",
                "linkedin_url": "https://linkedin.com/in/h",
                "stage": "identified",
            },
            headers=user_b_headers,
        )
        assert resp.status_code == 403

        # User B tries to update a person in Workspace A
        resp = await client.patch(
            f"/api/v1/people/{person_a_id}?workspace_id={workspace_a_id}",
            json={"name": "Hacked Name"},
            headers=user_b_headers,
        )
        assert resp.status_code == 403

        # User B tries to delete a person in Workspace A
        resp = await client.delete(
            f"/api/v1/people/{person_a_id}?workspace_id={workspace_a_id}", headers=user_b_headers
        )
        assert resp.status_code == 403

        # User B tries to list activities for a person in Workspace A
        resp = await client.get(
            f"/api/v1/people/{person_a_id}/activities?workspace_id={workspace_a_id}",
            headers=user_b_headers,
        )
        assert resp.status_code == 403

        # User B tries to create an activity in Workspace A
        resp = await client.post(
            f"/api/v1/people/{person_a_id}/activities?workspace_id={workspace_a_id}",
            json={"action_type": "note", "source": "web", "notes": "Hacked Note"},
            headers=user_b_headers,
        )
        assert resp.status_code == 403

        # User B tries to get dashboard summary in Workspace A
        resp = await client.get(
            f"/api/v1/dashboard/summary?workspace_id={workspace_a_id}", headers=user_b_headers
        )
        assert resp.status_code == 403

        # User B tries to get dashboard due in Workspace A
        resp = await client.get(
            f"/api/v1/dashboard/due?workspace_id={workspace_a_id}", headers=user_b_headers
        )
        assert resp.status_code == 403

        # User B tries to get calendar link in Workspace A
        resp = await client.get(
            f"/api/v1/calendar/daily-reminder-link?workspace_id={workspace_a_id}",
            headers=user_b_headers,
        )
        assert resp.status_code == 403

        # User B tries to perform extension quick-action in Workspace A
        resp = await client.post(
            "/api/v1/extension/quick-action",
            json={
                "workspace_id": workspace_a_id,
                "person_id": person_a_id,
                "action_type": "accepted",
            },
            headers=user_b_headers,
        )
        assert resp.status_code == 403

    async def test_owner_only_update(self, client: AsyncClient, mock_headers: dict):
        # Create workspace A (User A is owner)
        resp = await client.post(
            "/api/v1/workspaces", json={"name": "Workspace A"}, headers=mock_headers
        )
        assert resp.status_code == 201
        workspace_a_id = resp.json()["id"]

        # To properly test owner-only updates, we need a member who isn't the owner.
        # But MVP V1 doesn't have team invite endpoints yet.
        # This test ensures at least cross-workspace update is blocked (403).
        user_b_headers = {"Authorization": "Bearer user_b:user_b@example.com"}
        resp = await client.patch(
            f"/api/v1/workspaces/{workspace_a_id}", json={"name": "Hacked"}, headers=user_b_headers
        )
        assert resp.status_code == 403
