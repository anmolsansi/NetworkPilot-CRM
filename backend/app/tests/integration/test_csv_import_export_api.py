import logging
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.import_job import ImportJob
from app.worker import IMPORT_BATCH_SIZE, process_job

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)


@pytest.mark.anyio
class TestCsvImportExportAPI:
    async def _queue_and_process(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        headers: dict,
        workspace_id: str,
        file_name: str,
        csv_content: str,
        duplicate_strategy: str = "skip",
    ) -> dict:
        queued = await client.post(
            "/api/v1/imports/people/commit",
            data={
                "workspace_id": workspace_id,
                "duplicate_strategy": duplicate_strategy,
            },
            files={"file": (file_name, csv_content, "text/csv")},
            headers=headers,
        )
        assert queued.status_code == 200, queued.text
        assert queued.json()["status"] == "pending"
        job = await db_session.get(ImportJob, uuid.UUID(queued.json()["id"]))
        assert job is not None
        job.status = "processing"
        job.attempt_count += 1
        await db_session.commit()
        await process_job(db_session, job)
        status = await client.get(
            f"/api/v1/imports/{job.id}?workspace_id={workspace_id}", headers=headers
        )
        assert status.status_code == 200
        return status.json()

    async def test_commits_a_preview_in_multiple_chunks(
        self,
        client: AsyncClient,
        mock_headers: dict,
        db_session: AsyncSession,
    ):
        workspace_response = await client.post(
            "/api/v1/workspaces",
            json={"name": "Batched Import Workspace"},
            headers=mock_headers,
        )
        workspace_id = workspace_response.json()["id"]
        rows = [
            f"Batch {index},https://linkedin.com/in/batch-{index}/"
            for index in range(IMPORT_BATCH_SIZE + 1)
        ]
        csv_content = "name,linkedin_url\n" + "\n".join(rows) + "\n"
        job = await self._queue_and_process(
            client, db_session, mock_headers, workspace_id, "batched.csv", csv_content
        )
        assert job["status"] == "completed"
        assert job["processed_rows"] == IMPORT_BATCH_SIZE + 1
        assert job["failed_rows"] == 0

        people_response = await client.get(
            f"/api/v1/people?workspace_id={workspace_id}",
            headers=mock_headers,
        )
        assert people_response.json()["total"] == IMPORT_BATCH_SIZE + 1

    async def test_updates_exported_profiles_across_multiple_chunks(
        self,
        client: AsyncClient,
        mock_headers: dict,
        db_session: AsyncSession,
    ):
        workspace_response = await client.post(
            "/api/v1/workspaces",
            json={"name": "Batched Update Workspace"},
            headers=mock_headers,
        )
        workspace_id = workspace_response.json()["id"]
        initial_rows = [
            (
                f"Update {index},https://linkedin.com/in/update-{index}/,"
                f"Engineer,original-{index}@example.com"
            )
            for index in range(IMPORT_BATCH_SIZE + 1)
        ]
        initial_csv = "name,linkedin_url,current_role,email\n" + "\n".join(initial_rows) + "\n"
        initial_job = await self._queue_and_process(
            client,
            db_session,
            mock_headers,
            workspace_id,
            "initial.csv",
            initial_csv,
        )
        assert initial_job["failed_rows"] == 0

        export_response = await client.get(
            f"/api/v1/exports/people.csv?workspace_id={workspace_id}",
            headers=mock_headers,
        )
        assert export_response.status_code == 200
        assert export_response.text.splitlines()[0].split(",")[0] == "id"

        people_before = await client.get(
            f"/api/v1/people?workspace_id={workspace_id}&limit=100",
            headers=mock_headers,
        )
        people = people_before.json()["items"]
        updated_emails = {
            person["id"]: f"updated-{index}@example.com" for index, person in enumerate(people)
        }
        update_csv = (
            "id,email\n"
            + "\n".join(f"{person_id},{email}" for person_id, email in updated_emails.items())
            + "\n"
        )

        update_job = await self._queue_and_process(
            client,
            db_session,
            mock_headers,
            workspace_id,
            "updates.csv",
            update_csv,
            duplicate_strategy="update",
        )
        assert update_job["status"] == "completed"
        assert update_job["processed_rows"] == IMPORT_BATCH_SIZE + 1
        assert update_job["failed_rows"] == 0

        people_after = await client.get(
            f"/api/v1/people?workspace_id={workspace_id}&limit=100",
            headers=mock_headers,
        )
        updated_people = people_after.json()["items"]
        assert people_after.json()["total"] == IMPORT_BATCH_SIZE + 1
        assert all(person["email"] == updated_emails[person["id"]] for person in updated_people)
        assert all(person["role"] == "Engineer" for person in updated_people)

    async def test_imports_octopus_connect_export_columns(
        self,
        client: AsyncClient,
        mock_headers: dict,
        db_session: AsyncSession,
    ):
        workspace_response = await client.post(
            "/api/v1/workspaces",
            json={"name": "Octopus Workspace"},
            headers=mock_headers,
        )
        workspace_id = workspace_response.json()["id"]
        csv_content = (
            "Link,First name,Last name,Company,Position,Email,Phone number,Premium,"
            "Location,Company website,Processed at,Processed at millis,Invite accepted at,"
            "Invite accepted at millis\n"
            "https://linkedin.com/in/benbang/,Benjamin,Bang,Brex,Engineering Manager,"
            "ben@example.com,+1 555 0100,Yes,San Francisco Bay Area,https://brex.com/,"
            "Jul 06 2026 11:06 PM,1783359397124,,\n"
        )
        preview_response = await client.post(
            "/api/v1/imports/people/preview",
            data={"workspace_id": workspace_id},
            files={"file": ("octopus.csv", csv_content, "text/csv")},
            headers=mock_headers,
        )
        assert preview_response.status_code == 200
        preview = preview_response.json()
        row = preview["rows"][0]
        assert row["status"] == "valid"
        assert row["name"] == "Benjamin Bang"
        assert row["current_role"] == "Engineering Manager"
        assert row["phone_number"] == "+1 555 0100"
        assert row["premium"] is True
        assert row["processed_at_millis"] == 1783359397124

        job = await self._queue_and_process(
            client, db_session, mock_headers, workspace_id, "octopus.csv", csv_content
        )
        assert job["status"] == "completed"
        people_response = await client.get(
            f"/api/v1/people?workspace_id={workspace_id}", headers=mock_headers
        )
        person_id = people_response.json()["items"][0]["id"]
        person_response = await client.get(
            f"/api/v1/people/{person_id}?workspace_id={workspace_id}",
            headers=mock_headers,
        )
        assert person_response.status_code == 200
        person = person_response.json()
        assert person["first_name"] == "Benjamin"
        assert person["last_name"] == "Bang"
        assert person["email"] == "ben@example.com"
        assert person["company_website"] == "https://brex.com/"

    async def test_preview_commit_and_export_people_csv(
        self,
        client: AsyncClient,
        mock_headers: dict,
        db_session: AsyncSession,
    ):
        workspace_response = await client.post(
            "/api/v1/workspaces",
            json={"name": "CSV Workspace"},
            headers=mock_headers,
        )
        assert workspace_response.status_code == 201
        workspace_id = workspace_response.json()["id"]

        csv_content = (
            "name,linkedin_url,current_role,current_company,tags\n"
            "Ada Lovelace,https://www.linkedin.com/in/ada-lovelace/,Engineer,Example Inc,"
            "backend;referral\n"
        )
        preview_response = await client.post(
            "/api/v1/imports/people/preview",
            data={
                "workspace_id": workspace_id,
                "default_initial_action_type": "invite_sent",
                "duplicate_strategy": "skip",
                "default_priority": "B",
            },
            files={"file": ("people.csv", csv_content, "text/csv")},
            headers=mock_headers,
        )
        assert preview_response.status_code == 200
        preview = preview_response.json()
        assert preview["summary"]["valid_rows"] == 1
        assert preview["rows"][0]["normalized_profile_url"] == "linkedin.com/in/ada-lovelace"

        job = await self._queue_and_process(
            client, db_session, mock_headers, workspace_id, "people.csv", csv_content
        )
        assert job["status"] == "completed"
        assert job["processed_rows"] == 1

        export_response = await client.get(
            f"/api/v1/exports/people.csv?workspace_id={workspace_id}",
            headers=mock_headers,
        )
        assert export_response.status_code == 200
        assert export_response.headers["content-type"].startswith("text/csv")
        assert "Ada Lovelace" in export_response.text
        assert "linkedin.com/in/ada-lovelace" in export_response.text
