import logging
import pytest
from httpx import AsyncClient



_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
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
