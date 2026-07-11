import logging
import pytest
from httpx import AsyncClient



_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
@pytest.mark.anyio
class TestCsvImportExportAPI:
    async def test_imports_octopus_connect_export_columns(
        self,
        client: AsyncClient,
        mock_headers: dict,
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

        commit_response = await client.post(
            "/api/v1/imports/people/commit",
            json={
                "workspace_id": workspace_id,
                "import_batch_id": preview["import_batch_id"],
                "rows": [row],
            },
            headers=mock_headers,
        )
        assert commit_response.status_code == 200
        person_id = commit_response.json()["created_people"][0]["id"]
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

        commit_response = await client.post(
            "/api/v1/imports/people/commit",
            json={
                "workspace_id": workspace_id,
                "default_initial_action_type": "invite_sent",
                "duplicate_strategy": "skip",
                "default_priority": "B",
                "import_batch_id": preview["import_batch_id"],
                "rows": [
                    {
                        "name": "Ada Lovelace",
                        "linkedin_url": "https://www.linkedin.com/in/ada-lovelace/",
                        "current_role": "Engineer",
                        "current_company": "Example Inc",
                    }
                ],
            },
            headers=mock_headers,
        )
        assert commit_response.status_code == 200
        assert commit_response.json()["summary"]["created_count"] == 1

        export_response = await client.get(
            f"/api/v1/exports/people.csv?workspace_id={workspace_id}",
            headers=mock_headers,
        )
        assert export_response.status_code == 200
        assert export_response.headers["content-type"].startswith("text/csv")
        assert "Ada Lovelace" in export_response.text
        assert "linkedin.com/in/ada-lovelace" in export_response.text
