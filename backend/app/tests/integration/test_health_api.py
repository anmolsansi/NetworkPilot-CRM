import pytest
from httpx import AsyncClient


@pytest.mark.anyio
class TestHealthEndpoint:
    async def test_health_returns_ok(self, client: AsyncClient):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "networkpilot-api"


@pytest.mark.anyio
class TestMeEndpoint:
    async def test_me_requires_auth(self, client: AsyncClient):
        response = await client.get("/api/v1/me")
        assert response.status_code in [401, 422]

    async def test_me_with_invalid_token(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/me",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401
