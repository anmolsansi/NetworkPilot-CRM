import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.background_job import BackgroundJob
from app.worker import process_background_job


@pytest.mark.anyio
class TestV001ToV010Completion:
    async def _workspace(self, client: AsyncClient, headers: dict, name: str) -> str:
        response = await client.post("/api/v1/workspaces", json={"name": name}, headers=headers)
        assert response.status_code == 201
        return response.json()["id"]

    async def _person(
        self,
        client: AsyncClient,
        headers: dict,
        workspace_id: str,
        name: str,
        **values,
    ) -> dict:
        payload = {
            "name": name,
            "linkedin_url": (
                f"https://linkedin.com/in/{name.lower().replace(' ', '-')}-{uuid.uuid4()}/"
            ),
            **values,
        }
        response = await client.post(
            f"/api/v1/people?workspace_id={workspace_id}", json=payload, headers=headers
        )
        assert response.status_code == 201, response.text
        return response.json()

    async def test_saved_views_are_allowlisted_unique_and_user_scoped(
        self, client: AsyncClient, mock_headers: dict
    ):
        workspace_id = await self._workspace(client, mock_headers, "Saved View Completion")
        payload = {
            "name": "Favourite leaders",
            "filters": {"favorite": "true", "role": "leader"},
            "sort_by": "company",
            "sort_order": "asc",
        }
        created = await client.post(
            f"/api/v1/saved-views?workspace_id={workspace_id}",
            json=payload,
            headers=mock_headers,
        )
        assert created.status_code == 201
        duplicate = await client.post(
            f"/api/v1/saved-views?workspace_id={workspace_id}",
            json=payload,
            headers=mock_headers,
        )
        assert duplicate.status_code == 409
        unsafe = await client.post(
            f"/api/v1/saved-views?workspace_id={workspace_id}",
            json={**payload, "name": "Unsafe", "filters": {"workspace_id": "other"}},
            headers=mock_headers,
        )
        assert unsafe.status_code == 422

    async def test_duplicate_detection_merge_and_field_allowlist(
        self, client: AsyncClient, mock_headers: dict
    ):
        workspace_id = await self._workspace(client, mock_headers, "Duplicate Completion")
        target = await self._person(
            client,
            mock_headers,
            workspace_id,
            "Ada Lovelace",
            first_name="Ada",
            last_name="Lovelace",
            company="Analytical Engines",
        )
        source = await self._person(
            client,
            mock_headers,
            workspace_id,
            "Ada L",
            first_name="Ada",
            last_name="Lovelace",
            company="Analytical Engines",
            email="ada@example.com",
        )
        groups = await client.get(
            f"/api/v1/people/duplicates?workspace_id={workspace_id}", headers=mock_headers
        )
        assert groups.status_code == 200
        assert {target["id"], source["id"]} <= {
            person["id"] for group in groups.json() for person in group["people"]
        }
        unsafe = await client.post(
            f"/api/v1/people/duplicates/merge?workspace_id={workspace_id}",
            json={
                "target_person_id": target["id"],
                "source_person_id": source["id"],
                "fields_to_keep_from_source": ["workspace_id"],
            },
            headers=mock_headers,
        )
        assert unsafe.status_code == 422
        merged = await client.post(
            f"/api/v1/people/duplicates/merge?workspace_id={workspace_id}",
            json={
                "target_person_id": target["id"],
                "source_person_id": source["id"],
                "fields_to_keep_from_source": ["email"],
            },
            headers=mock_headers,
        )
        assert merged.status_code == 200
        assert merged.json()["target_person"]["email"] == "ada@example.com"

    async def test_tags_pipeline_custom_fields_and_tenant_boundaries(
        self, client: AsyncClient, mock_headers: dict
    ):
        workspace_id = await self._workspace(client, mock_headers, "Configuration Completion")
        other_workspace_id = await self._workspace(client, mock_headers, "Other Configuration")
        tag = await client.post(
            "/api/v1/tags",
            json={"workspace_id": workspace_id, "name": "VIP", "color": "#ff0000"},
            headers=mock_headers,
        )
        assert tag.status_code == 200
        tag_id = tag.json()["id"]
        updated_tag = await client.patch(
            f"/api/v1/tags/{tag_id}?workspace_id={workspace_id}",
            json={"color": "#00aa00"},
            headers=mock_headers,
        )
        assert updated_tag.json()["color"] == "#00aa00"

        first_stage = await client.post(
            f"/api/v1/pipeline-stages?workspace_id={workspace_id}",
            json={"name": "Prospect", "order": 0, "color": "#112233"},
            headers=mock_headers,
        )
        second_stage = await client.post(
            f"/api/v1/pipeline-stages?workspace_id={workspace_id}",
            json={"name": "Contacted", "order": 1, "color": "#334455"},
            headers=mock_headers,
        )
        assert first_stage.status_code == second_stage.status_code == 201
        await client.patch(
            f"/api/v1/pipeline-stages/{first_stage.json()['id']}?workspace_id={workspace_id}",
            json={"allowed_next_stage_ids": [second_stage.json()["id"]]},
            headers=mock_headers,
        )

        custom_field = await client.post(
            f"/api/v1/custom-fields?workspace_id={workspace_id}",
            json={
                "name": "Relationship",
                "field_type": "select",
                "options": {"choices": ["Warm", "Cold"]},
            },
            headers=mock_headers,
        )
        assert custom_field.status_code == 201
        person = await self._person(
            client,
            mock_headers,
            workspace_id,
            "Configured Person",
            tag_ids=[tag_id],
            stage_id=first_stage.json()["id"],
            custom_fields_data={custom_field.json()["id"]: "Warm"},
        )
        list_response = await client.get(
            f"/api/v1/people?workspace_id={workspace_id}&tag_ids={tag_id}",
            headers=mock_headers,
        )
        assert list_response.json()["total"] == 1
        invalid_value = await client.patch(
            f"/api/v1/people/{person['id']}?workspace_id={workspace_id}",
            json={"custom_fields_data": {custom_field.json()["id"]: "Invalid"}},
            headers=mock_headers,
        )
        assert invalid_value.status_code == 422
        cross_workspace = await self._person(
            client,
            mock_headers,
            other_workspace_id,
            "Cross Workspace Person",
        )
        rejected = await client.patch(
            f"/api/v1/people/{cross_workspace['id']}?workspace_id={other_workspace_id}",
            json={"tag_ids": [tag_id]},
            headers=mock_headers,
        )
        assert rejected.status_code == 422

    async def test_extension_favourite_trash_restore_and_unarchive(
        self, client: AsyncClient, mock_headers: dict
    ):
        workspace_id = await self._workspace(client, mock_headers, "Restore Completion")
        person = await self._person(client, mock_headers, workspace_id, "Favourite Person")
        favourite = await client.post(
            "/api/v1/extension/favorite",
            json={
                "workspace_id": workspace_id,
                "person_id": person["id"],
                "is_favorite": True,
                "favorite_notes": "Important relationship",
            },
            headers=mock_headers,
        )
        assert favourite.status_code == 200
        assert favourite.json()["is_favorite"] is True

        active_restore = await client.post(
            f"/api/v1/people/{person['id']}/restore?workspace_id={workspace_id}",
            headers=mock_headers,
        )
        assert active_restore.status_code == 422
        await client.delete(
            f"/api/v1/people/{person['id']}?workspace_id={workspace_id}", headers=mock_headers
        )
        trash = await client.get(
            f"/api/v1/people?workspace_id={workspace_id}&deleted_only=true",
            headers=mock_headers,
        )
        assert [item["id"] for item in trash.json()["items"]] == [person["id"]]
        restored = await client.post(
            f"/api/v1/people/{person['id']}/restore?workspace_id={workspace_id}",
            headers=mock_headers,
        )
        assert restored.status_code == 200
        await client.post(
            f"/api/v1/people/{person['id']}/archive?workspace_id={workspace_id}",
            json={},
            headers=mock_headers,
        )
        unarchived = await client.post(
            f"/api/v1/people/{person['id']}/unarchive?workspace_id={workspace_id}",
            headers=mock_headers,
        )
        assert unarchived.json()["status"] == "active"

    async def test_digest_creates_in_app_notification(
        self,
        client: AsyncClient,
        mock_headers: dict,
        db_session: AsyncSession,
    ):
        workspace_id = await self._workspace(client, mock_headers, "Notification Completion")
        person = await self._person(client, mock_headers, workspace_id, "Due Person")
        due_date = date.today() - timedelta(days=1)
        await client.post(
            "/api/v1/people/bulk-actions",
            json={
                "workspace_id": workspace_id,
                "person_ids": [person["id"]],
                "action": "set_next_action",
                "payload": {"next_action_type": "follow_up", "next_action_date": str(due_date)},
            },
            headers=mock_headers,
        )
        result = await db_session.execute(
            select(BackgroundJob).where(BackgroundJob.workspace_id == uuid.UUID(workspace_id))
        )
        job = result.scalars().first()
        assert job is not None
        await process_background_job(db_session, job)
        notifications = await client.get(
            f"/api/v1/notifications?workspace_id={workspace_id}", headers=mock_headers
        )
        assert notifications.status_code == 200
        assert notifications.json()[0]["notification_type"] == "overdue_alert"
