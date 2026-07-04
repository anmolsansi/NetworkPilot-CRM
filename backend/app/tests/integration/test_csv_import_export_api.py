import pytest
from httpx import AsyncClient


@pytest.mark.anyio
class TestCsvImportExportAPI:
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
