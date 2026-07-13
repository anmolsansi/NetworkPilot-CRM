import logging
import uuid

import pytest
from httpx import AsyncClient

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)


@pytest.mark.anyio
class TestPeopleAPI:
    async def _create_people(
        self,
        client: AsyncClient,
        headers: dict,
        workspace_name: str,
        count: int = 2,
        tags: list[str] | None = None,
    ) -> tuple[str, list[dict]]:
        workspace_response = await client.post(
            "/api/v1/workspaces",
            json={"name": workspace_name},
            headers=headers,
        )
        workspace_id = workspace_response.json()["id"]
        tag_ids: list[str] = []
        for tag_name in tags or []:
            tag_response = await client.post(
                "/api/v1/tags",
                json={"workspace_id": workspace_id, "name": tag_name},
                headers=headers,
            )
            assert tag_response.status_code == 200
            tag_ids.append(tag_response.json()["id"])
        people: list[dict] = []
        for index in range(count):
            response = await client.post(
                f"/api/v1/people?workspace_id={workspace_id}",
                json={
                    "name": f"Bulk Person {index}",
                    "linkedin_url": f"https://linkedin.com/in/bulk-person-{uuid.uuid4()}/",
                    "tag_ids": tag_ids,
                },
                headers=headers,
            )
            assert response.status_code == 201
            people.append(response.json())
        return workspace_id, people

    async def test_bulk_actions_update_people_in_request_order(
        self,
        client: AsyncClient,
        mock_headers: dict,
    ):
        workspace_id, people = await self._create_people(
            client, mock_headers, "Bulk Actions Workspace", tags=["existing"]
        )
        person_ids = [people[1]["id"], people[0]["id"]]

        actions = [
            ("set_favorite", {"is_favorite": True}),
            ("add_tags", {"tags": ["new", "new", " spaced "]}),
            ("remove_tags", {"tags": ["existing"]}),
            ("set_priority", {"priority": "A"}),
            (
                "set_next_action",
                {"next_action_type": " send_message ", "next_action_date": "2026-08-01"},
            ),
        ]
        last_response = None
        for action, payload in actions:
            last_response = await client.post(
                "/api/v1/people/bulk-actions",
                json={
                    "workspace_id": workspace_id,
                    "person_ids": person_ids,
                    "action": action,
                    "payload": payload,
                },
                headers=mock_headers,
            )
            assert last_response.status_code == 200, last_response.text
            assert last_response.json()["updated_count"] == 2
            assert [item["id"] for item in last_response.json()["items"]] == person_ids

        assert last_response is not None
        for person in last_response.json()["items"]:
            assert person["is_favorite"] is True
            assert {tag["name"] for tag in person["tags"]} == {"new", "spaced"}
            assert person["priority"] == "A"
            assert person["next_action_type"] == "send_message"
            assert person["next_action_date"] == "2026-08-01"

        for priority in ("B", "C", "A"):
            priority_response = await client.post(
                "/api/v1/people/bulk-actions",
                json={
                    "workspace_id": workspace_id,
                    "person_ids": person_ids,
                    "action": "set_priority",
                    "payload": {"priority": priority},
                },
                headers=mock_headers,
            )
            assert priority_response.status_code == 200
            assert all(item["priority"] == priority for item in priority_response.json()["items"])

        clear_response = await client.post(
            "/api/v1/people/bulk-actions",
            json={
                "workspace_id": workspace_id,
                "person_ids": person_ids,
                "action": "set_next_action",
                "payload": {"next_action_type": None, "next_action_date": None},
            },
            headers=mock_headers,
        )
        assert clear_response.status_code == 200
        assert all(item["next_action_type"] is None for item in clear_response.json()["items"])

    async def test_bulk_stage_and_archive_create_activities(
        self,
        client: AsyncClient,
        mock_headers: dict,
    ):
        workspace_id, people = await self._create_people(
            client, mock_headers, "Bulk Activity Workspace", count=1
        )
        person_id = people[0]["id"]

        stage_response = await client.post(
            "/api/v1/people/bulk-actions",
            json={
                "workspace_id": workspace_id,
                "person_ids": [person_id],
                "action": "set_stage",
                "payload": {"stage": "accepted"},
            },
            headers=mock_headers,
        )
        assert stage_response.status_code == 200
        assert stage_response.json()["items"][0]["stage"] == "accepted"
        assert stage_response.json()["items"][0]["status"] == "active"
        assert stage_response.json()["items"][0]["last_action_type"] == "bulk_stage_change"

        await client.post(
            "/api/v1/people/bulk-actions",
            json={
                "workspace_id": workspace_id,
                "person_ids": [person_id],
                "action": "set_next_action",
                "payload": {"next_action_type": "follow_up", "next_action_date": "2026-08-02"},
            },
            headers=mock_headers,
        )
        stage_archive_response = await client.post(
            "/api/v1/people/bulk-actions",
            json={
                "workspace_id": workspace_id,
                "person_ids": [person_id],
                "action": "set_stage",
                "payload": {"stage": "archived"},
            },
            headers=mock_headers,
        )
        assert stage_archive_response.status_code == 200
        stage_archived = stage_archive_response.json()["items"][0]
        assert stage_archived["status"] == "archived"
        assert stage_archived["next_action_type"] is None
        assert stage_archived["next_action_date"] is None

        reactivate_response = await client.post(
            "/api/v1/people/bulk-actions",
            json={
                "workspace_id": workspace_id,
                "person_ids": [person_id],
                "action": "set_stage",
                "payload": {"stage": "accepted"},
            },
            headers=mock_headers,
        )
        assert reactivate_response.status_code == 200
        assert reactivate_response.json()["items"][0]["status"] == "active"

        archive_response = await client.post(
            "/api/v1/people/bulk-actions",
            json={
                "workspace_id": workspace_id,
                "person_ids": [person_id],
                "action": "archive",
                "payload": {},
            },
            headers=mock_headers,
        )
        assert archive_response.status_code == 200
        archived = archive_response.json()["items"][0]
        assert archived["stage"] == "archived"
        assert archived["status"] == "archived"
        assert archived["next_action_type"] is None
        assert archived["last_action_type"] == "bulk_archive"

        activities_response = await client.get(
            f"/api/v1/people/{person_id}/activities?workspace_id={workspace_id}",
            headers=mock_headers,
        )
        assert activities_response.status_code == 200
        assert {activity["action_type"] for activity in activities_response.json()} == {
            "bulk_archive",
            "bulk_stage_change",
        }
        assert all(activity["source"] == "web_app" for activity in activities_response.json())

    async def test_bulk_action_validation_and_atomic_workspace_failure(
        self,
        client: AsyncClient,
        mock_headers: dict,
    ):
        workspace_id, people = await self._create_people(
            client,
            mock_headers,
            "Bulk Validation Workspace",
            count=2,
            tags=[f"tag-{index}" for index in range(20)],
        )
        person_id = people[0]["id"]
        deleted_person_id = people[1]["id"]
        other_workspace_id, other_people = await self._create_people(
            client, mock_headers, "Other Bulk Workspace", count=1
        )
        assert other_workspace_id != workspace_id

        atomic_response = await client.post(
            "/api/v1/people/bulk-actions",
            json={
                "workspace_id": workspace_id,
                "person_ids": [person_id, other_people[0]["id"]],
                "action": "set_favorite",
                "payload": {"is_favorite": True},
            },
            headers=mock_headers,
        )
        assert atomic_response.status_code == 404
        assert atomic_response.json()["error"]["message"] == "One or more people not found"
        unchanged = await client.get(
            f"/api/v1/people/{person_id}?workspace_id={workspace_id}", headers=mock_headers
        )
        assert unchanged.json()["is_favorite"] is False

        delete_response = await client.delete(
            f"/api/v1/people/{deleted_person_id}?workspace_id={workspace_id}",
            headers=mock_headers,
        )
        assert delete_response.status_code == 204
        deleted_atomic_response = await client.post(
            "/api/v1/people/bulk-actions",
            json={
                "workspace_id": workspace_id,
                "person_ids": [person_id, deleted_person_id],
                "action": "set_favorite",
                "payload": {"is_favorite": True},
            },
            headers=mock_headers,
        )
        assert deleted_atomic_response.status_code == 404
        still_unchanged = await client.get(
            f"/api/v1/people/{person_id}?workspace_id={workspace_id}", headers=mock_headers
        )
        assert still_unchanged.json()["is_favorite"] is False

        too_many_tags = await client.post(
            "/api/v1/people/bulk-actions",
            json={
                "workspace_id": workspace_id,
                "person_ids": [person_id],
                "action": "add_tags",
                "payload": {"tags": ["overflow"]},
            },
            headers=mock_headers,
        )
        assert too_many_tags.status_code == 422
        assert too_many_tags.json()["error"]["message"] == "A person can have at most 20 tags."

        invalid_requests = [
            {"person_ids": []},
            {"person_ids": [person_id, person_id]},
            {"person_ids": [str(uuid.uuid4()) for _ in range(101)]},
        ]
        for override in invalid_requests:
            response = await client.post(
                "/api/v1/people/bulk-actions",
                json={
                    "workspace_id": workspace_id,
                    "person_ids": override["person_ids"],
                    "action": "set_favorite",
                    "payload": {"is_favorite": True},
                },
                headers=mock_headers,
            )
            assert response.status_code == 422

        unknown_field = await client.post(
            "/api/v1/people/bulk-actions",
            json={
                "workspace_id": workspace_id,
                "person_ids": [person_id],
                "action": "set_priority",
                "payload": {"priority": "A", "unexpected": True},
            },
            headers=mock_headers,
        )
        assert unknown_field.status_code == 422

        invalid_payloads = [
            {
                "action": "set_favorite",
                "payload": {"priority": "A"},
            },
            {
                "action": "add_tags",
                "payload": {"tags": ["x" * 51]},
            },
            {
                "action": "set_next_action",
                "payload": {"next_action_type": f" {'x' * 101} ", "next_action_date": None},
            },
        ]
        for invalid in invalid_payloads:
            response = await client.post(
                "/api/v1/people/bulk-actions",
                json={
                    "workspace_id": workspace_id,
                    "person_ids": [person_id],
                    **invalid,
                },
                headers=mock_headers,
            )
            assert response.status_code == 422

    async def test_bulk_action_requires_auth_and_workspace_membership(
        self,
        client: AsyncClient,
        mock_headers: dict,
    ):
        workspace_id, people = await self._create_people(
            client, mock_headers, "Bulk Auth Workspace", count=1
        )
        payload = {
            "workspace_id": workspace_id,
            "person_ids": [people[0]["id"]],
            "action": "set_favorite",
            "payload": {"is_favorite": True},
        }
        unauthenticated = await client.post("/api/v1/people/bulk-actions", json=payload)
        assert unauthenticated.status_code == 401

        forbidden = await client.post(
            "/api/v1/people/bulk-actions",
            json=payload,
            headers={"Authorization": "Bearer user-two:user-two@example.com"},
        )
        assert forbidden.status_code == 403

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
                "is_favorite": True,
                "favorite_notes": "Strong AI background",
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

        favorite_response = await client.get(
            "/api/v1/people",
            params={
                "workspace_id": workspace_id,
                "favorite": "true",
                "favorite_notes": "AI background",
            },
            headers=mock_headers,
        )
        assert favorite_response.status_code == 200
        assert favorite_response.json()["total"] == 1
        assert favorite_response.json()["items"][0]["first_name"] == "Zoe"
        assert favorite_response.json()["items"][0]["favorite_notes"] == "Strong AI background"

    async def test_list_people_requires_auth(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/people", params={"workspace_id": "00000000-0000-0000-0000-000000000000"}
        )
        assert response.status_code in [401, 422]

    async def test_create_person_requires_auth(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/people?workspace_id=00000000-0000-0000-0000-000000000000",
            json={"name": "Test Person", "linkedin_url": "https://www.linkedin.com/in/testperson/"},
        )
        assert response.status_code in [401, 422]


@pytest.mark.anyio
class TestActivitiesAPI:
    async def test_list_activities_requires_auth(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/people/00000000-0000-0000-0000-000000000000/activities",
            params={"workspace_id": "00000000-0000-0000-0000-000000000000"},
        )
        assert response.status_code in [401, 422]
