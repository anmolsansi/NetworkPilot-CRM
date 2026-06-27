import pytest
from httpx import AsyncClient

@pytest.mark.anyio
class TestMVPSmokeFlow:
    async def test_mvp_flow(self, client: AsyncClient, mock_headers: dict):
        # 1. Health check
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200

        # 2. Workspace create
        resp = await client.post("/api/v1/workspaces", json={"name": "Smoke Test Workspace"}, headers=mock_headers)
        assert resp.status_code == 201
        workspace_id = resp.json()["id"]

        # 3. Workspace list
        resp = await client.get("/api/v1/workspaces", headers=mock_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1
        assert resp.json()[0]["id"] == workspace_id

        # 4. Templates list
        resp = await client.get(f"/api/v1/templates?workspace_id={workspace_id}", headers=mock_headers)
        assert resp.status_code == 200

        # 5. Extension Lookup (not found)
        linkedin_url = "https://www.linkedin.com/in/smoketest"
        resp = await client.get(f"/api/v1/extension/lookup?workspace_id={workspace_id}&linkedin_url={linkedin_url}", headers=mock_headers)
        assert resp.status_code == 200
        assert resp.json()["found"] is False

        # 6. Extension Quick Create
        resp = await client.post(f"/api/v1/extension/quick-create?workspace_id={workspace_id}", json={
            "workspace_id": workspace_id,
            "name": "Smoke Test Person",
            "linkedin_url": linkedin_url,
            "initial_action": "invite_sent"
        }, headers=mock_headers)
        if resp.status_code != 200:
            print(resp.json())
        assert resp.status_code == 200
        person_id = resp.json()["person_id"]

        # 7. Extension Lookup (found)
        resp = await client.get(f"/api/v1/extension/lookup?workspace_id={workspace_id}&linkedin_url={linkedin_url}", headers=mock_headers)
        assert resp.status_code == 200
        assert resp.json()["found"] is True
        assert resp.json()["person_id"] == person_id

        # 8. Person List
        resp = await client.get(f"/api/v1/people?workspace_id={workspace_id}", headers=mock_headers)
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 1
        assert resp.json()["items"][0]["id"] == person_id

        # 9. Extension Quick Action
        resp = await client.post(f"/api/v1/extension/quick-action?workspace_id={workspace_id}", json={
            "workspace_id": workspace_id,
            "person_id": person_id,
            "action_type": "accepted",
            "notes": "Looks good"
        }, headers=mock_headers)
        if resp.status_code != 200:
            print(resp.json())
        assert resp.status_code == 200
