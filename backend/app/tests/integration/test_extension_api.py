import logging
import pytest
from httpx import AsyncClient



_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
@pytest.mark.anyio
class TestDashboardAPI:
    async def test_summary_requires_auth(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/dashboard/summary",
            params={"workspace_id": "00000000-0000-0000-0000-000000000000"}
        )
        assert response.status_code in [401, 422]

    async def test_due_requires_auth(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/dashboard/due",
            params={"workspace_id": "00000000-0000-0000-0000-000000000000"}
        )
        assert response.status_code in [401, 422]


@pytest.mark.anyio
class TestTemplatesAPI:
    async def test_list_templates_requires_auth(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/templates",
            params={"workspace_id": "00000000-0000-0000-0000-000000000000"}
        )
        assert response.status_code in [401, 422]


@pytest.mark.anyio
class TestExtensionAPI:
    async def test_lookup_requires_auth(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/extension/lookup",
            params={
                "workspace_id": "00000000-0000-0000-0000-000000000000",
                "linkedin_url": "https://www.linkedin.com/in/test/"
            }
        )
        assert response.status_code in [401, 422]

    async def test_quick_create_requires_auth(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/extension/quick-create",
            json={
                "workspace_id": "00000000-0000-0000-0000-000000000000",
                "linkedin_url": "https://www.linkedin.com/in/test/",
                "name": "Test Person",
                "initial_action": "invite_sent"
            }
        )
        assert response.status_code in [401, 422]
