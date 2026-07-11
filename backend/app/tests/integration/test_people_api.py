import logging
import pytest
from httpx import AsyncClient



_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
@pytest.mark.anyio
class TestPeopleAPI:
    async def test_filters_and_sorts_people_columns(
        self,
        client: AsyncClient,
        mock_headers: dict,
    ):
        workspace_response = await client.post(
            "/api/v1/workspaces",
            json={"name": "Filter Workspace"},
            headers=mock_headers,
        )
        workspace_id = workspace_response.json()["id"]
        people = [
            {
                "name": "Zoe Zebra",
                "first_name": "Zoe",
                "linkedin_url": "https://linkedin.com/in/zoe-zebra/",
                "company": "Acme Labs",
                "role": "Engineer",
                "location": "Boston",
                "email": "zoe@example.com",
                "premium": True,
            },
            {
                "name": "Amy Alpha",
                "first_name": "Amy",
                "linkedin_url": "https://linkedin.com/in/amy-alpha/",
                "company": "Acme Labs",
                "role": "Manager",
                "location": "Austin",
                "email": "amy@example.com",
                "premium": False,
            },
            {
                "name": "Bob Beta",
                "first_name": "Bob",
                "linkedin_url": "https://linkedin.com/in/bob-beta/",
                "company": "Other Co",
                "role": "Engineer",
                "location": "Boston",
                "email": "bob@example.com",
                "premium": True,
            },
        ]
        for person in people:
            response = await client.post(
                f"/api/v1/people?workspace_id={workspace_id}",
                json=person,
                headers=mock_headers,
            )
            assert response.status_code == 201

        response = await client.get(
            "/api/v1/people",
            params={
                "workspace_id": workspace_id,
                "company": "acme",
                "sort_by": "first_name",
                "sort_order": "asc",
            },
            headers=mock_headers,
        )
        assert response.status_code == 200
        assert response.json()["total"] == 2
        assert [item["first_name"] for item in response.json()["items"]] == ["Amy", "Zoe"]

        premium_response = await client.get(
            "/api/v1/people",
            params={
                "workspace_id": workspace_id,
                "premium": "true",
                "location": "boston",
                "sort_by": "first_name",
                "sort_order": "asc",
            },
            headers=mock_headers,
        )
        assert premium_response.status_code == 200
        assert [item["first_name"] for item in premium_response.json()["items"]] == ["Bob", "Zoe"]

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
