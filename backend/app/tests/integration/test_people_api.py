import pytest
from httpx import AsyncClient


@pytest.mark.anyio
class TestPeopleAPI:
    async def test_list_people_requires_auth(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/people",
            params={"workspace_id": "00000000-0000-0000-0000-000000000000"}
        )
        assert response.status_code in [401, 422]

    async def test_create_person_requires_auth(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/people?workspace_id=00000000-0000-0000-0000-000000000000",
            json={
                "name": "Test Person",
                "linkedin_url": "https://www.linkedin.com/in/testperson/"
            }
        )
        assert response.status_code in [401, 422]


@pytest.mark.anyio
class TestActivitiesAPI:
    async def test_list_activities_requires_auth(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/people/00000000-0000-0000-0000-000000000000/activities",
            params={"workspace_id": "00000000-0000-0000-0000-000000000000"}
        )
        assert response.status_code in [401, 422]
