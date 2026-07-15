import uuid

import pytest
from httpx import AsyncClient

from app.api.routes import activities as activities_routes
from app.services.storage_service import StorageService


class FakeR2Client:
    def __init__(self):
        self.objects: dict[str, bytes] = {}

    def put_object(self, **kwargs):
        self.objects[kwargs["Key"]] = kwargs["Body"]
        return {"ETag": "test-etag"}

    def delete_object(self, **kwargs):
        self.objects.pop(kwargs["Key"], None)
        return {}

    def generate_presigned_url(self, operation, **kwargs):
        return (
            f"https://private-r2.example/{kwargs['Params']['Key']}"
            f"?expires={kwargs['ExpiresIn']}"
        )


@pytest.mark.anyio
async def test_private_r2_attachment_lifecycle_and_authorization(
    client: AsyncClient,
    mock_headers: dict,
    monkeypatch: pytest.MonkeyPatch,
):
    fake_r2 = FakeR2Client()
    storage = StorageService(client=fake_r2, bucket_name="test-attachments")
    monkeypatch.setattr(activities_routes, "StorageService", lambda: storage)

    workspace_response = await client.post(
        "/api/v1/workspaces",
        json={"name": "R2 Attachments"},
        headers=mock_headers,
    )
    workspace_id = workspace_response.json()["id"]
    person_response = await client.post(
        f"/api/v1/people?workspace_id={workspace_id}",
        json={
            "name": "Attachment Person",
            "linkedin_url": "https://linkedin.com/in/attachment-person",
        },
        headers=mock_headers,
    )
    activity_response = await client.post(
        f"/api/v1/people/{person_response.json()['id']}/activities"
        f"?workspace_id={workspace_id}",
        json={"action_type": "message_sent", "source": "web_app"},
        headers=mock_headers,
    )
    activity_id = activity_response.json()["id"]

    missing_activity_response = await client.post(
        f"/api/v1/activities/{uuid.uuid4()}/attachments?workspace_id={workspace_id}",
        files={"file": ("note.txt", b"safe text", "text/plain")},
        headers=mock_headers,
    )
    assert missing_activity_response.status_code == 404
    assert fake_r2.objects == {}

    spoofed_file_response = await client.post(
        f"/api/v1/activities/{activity_id}/attachments?workspace_id={workspace_id}",
        files={"file": ("document.pdf", b"not a pdf", "application/pdf")},
        headers=mock_headers,
    )
    assert spoofed_file_response.status_code == 422
    assert fake_r2.objects == {}

    upload_response = await client.post(
        f"/api/v1/activities/{activity_id}/attachments?workspace_id={workspace_id}",
        files={"file": ("document.pdf", b"%PDF-1.7\nprivate", "application/pdf")},
        headers=mock_headers,
    )
    assert upload_response.status_code == 200
    attachment = upload_response.json()
    assert attachment["file_size"] == len(b"%PDF-1.7\nprivate")
    assert len(fake_r2.objects) == 1
    object_key = next(iter(fake_r2.objects))
    assert object_key.startswith(
        f"workspaces/{workspace_id}/activities/{activity_id}/"
    )

    outsider_headers = {"Authorization": "Bearer outsider:outsider@example.com"}
    outsider_response = await client.get(
        f"/api/v1/attachments/{attachment['id']}/download-url"
        f"?workspace_id={workspace_id}",
        headers=outsider_headers,
    )
    assert outsider_response.status_code == 403

    download_response = await client.get(
        f"/api/v1/attachments/{attachment['id']}/download-url"
        f"?workspace_id={workspace_id}",
        headers=mock_headers,
    )
    assert download_response.status_code == 200
    assert download_response.json()["expires_in"] == 300
    assert download_response.json()["url"].startswith("https://private-r2.example/")

    delete_response = await client.delete(
        f"/api/v1/attachments/{attachment['id']}?workspace_id={workspace_id}",
        headers=mock_headers,
    )
    assert delete_response.status_code == 204
    assert fake_r2.objects == {}

    missing_download_response = await client.get(
        f"/api/v1/attachments/{attachment['id']}/download-url"
        f"?workspace_id={workspace_id}",
        headers=mock_headers,
    )
    assert missing_download_response.status_code == 404

    second_upload_response = await client.post(
        f"/api/v1/activities/{activity_id}/attachments?workspace_id={workspace_id}",
        files={"file": ("activity.txt", b"delete with activity", "text/plain")},
        headers=mock_headers,
    )
    second_attachment_id = second_upload_response.json()["id"]
    assert len(fake_r2.objects) == 1

    activity_delete_response = await client.delete(
        f"/api/v1/activities/{activity_id}?workspace_id={workspace_id}",
        headers=mock_headers,
    )
    assert activity_delete_response.status_code == 204
    assert fake_r2.objects == {}
    deleted_activity_download = await client.get(
        f"/api/v1/attachments/{second_attachment_id}/download-url"
        f"?workspace_id={workspace_id}",
        headers=mock_headers,
    )
    assert deleted_activity_download.status_code == 404
