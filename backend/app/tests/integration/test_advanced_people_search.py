import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_people_search_covers_profile_activity_tag_and_custom_fields(
    client: AsyncClient,
    mock_headers: dict,
):
    workspace_response = await client.post(
        "/api/v1/workspaces",
        json={"name": "Advanced Search"},
        headers=mock_headers,
    )
    workspace_id = workspace_response.json()["id"]

    tag_response = await client.post(
        "/api/v1/tags",
        json={"workspace_id": workspace_id, "name": "quantum-network"},
        headers=mock_headers,
    )
    assert tag_response.status_code == 200
    custom_field_response = await client.post(
        f"/api/v1/custom-fields?workspace_id={workspace_id}",
        json={"name": "Initiative", "field_type": "text"},
        headers=mock_headers,
    )
    assert custom_field_response.status_code == 201
    custom_field_id = custom_field_response.json()["id"]

    target_response = await client.post(
        f"/api/v1/people?workspace_id={workspace_id}",
        json={
            "name": "Katherine Johnson",
            "linkedin_url": "https://linkedin.com/in/advanced-search-target",
            "phone_number": "+1 555 0199",
            "company_website": "https://orbital-labs.example",
            "favorite_notes": "Board champion",
            "notes": "Interested in distributed systems",
            "processed_at": "2026-06-03T10:00:00Z",
            "tag_ids": [tag_response.json()["id"]],
            "custom_fields_data": {custom_field_id: "Project Aurora"},
        },
        headers=mock_headers,
    )
    assert target_response.status_code == 201
    target_id = target_response.json()["id"]

    await client.post(
        f"/api/v1/people?workspace_id={workspace_id}",
        json={
            "name": "Unrelated Person",
            "linkedin_url": "https://linkedin.com/in/advanced-search-distractor",
        },
        headers=mock_headers,
    )
    activity_response = await client.post(
        f"/api/v1/people/{target_id}/activities?workspace_id={workspace_id}",
        json={
            "action_type": "message_sent",
            "source": "web_app",
            "message": "Sent the nebula-briefing document",
            "notes": "Discussed observability strategy",
        },
        headers=mock_headers,
    )
    assert activity_response.status_code == 201

    search_terms = (
        "555 0199",
        "orbital-labs",
        "Board champion",
        "distributed systems",
        "quantum-network",
        "Project Aurora",
        "nebula-briefing",
        "observability strategy",
        "2026-06-03",
    )
    for term in search_terms:
        response = await client.get(
            "/api/v1/people",
            params={"workspace_id": workspace_id, "search": term},
            headers=mock_headers,
        )
        assert response.status_code == 200, term
        assert response.json()["total"] == 1, term
        assert response.json()["items"][0]["id"] == target_id, term
