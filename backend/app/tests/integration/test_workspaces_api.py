import pytest
from httpx import AsyncClient


@pytest.mark.anyio
class TestWorkspacesAPI:
    async def test_list_workspaces_requires_auth(self, client: AsyncClient):
        response = await client.get("/api/v1/workspaces")
        assert response.status_code in [401, 422]

    async def test_create_workspace_requires_auth(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/workspaces",
            json={"name": "Test Workspace"}
        )
        assert response.status_code in [401, 422]
