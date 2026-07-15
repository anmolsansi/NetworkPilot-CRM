from datetime import date, timedelta

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_activity_timeline_filters_by_type_source_and_date(
    client: AsyncClient,
    mock_headers: dict,
):
    workspace_response = await client.post(
        "/api/v1/workspaces",
        json={"name": "Activity Filters"},
        headers=mock_headers,
    )
    workspace_id = workspace_response.json()["id"]
    person_response = await client.post(
        f"/api/v1/people?workspace_id={workspace_id}",
        json={
            "name": "Timeline Person",
            "linkedin_url": "https://linkedin.com/in/timeline-filter-person",
        },
        headers=mock_headers,
    )
    person_id = person_response.json()["id"]

    for action_type, source in (
        ("message_sent", "web_app"),
        ("reply_received", "chrome_extension"),
        ("follow_up_1_sent", "web_app"),
    ):
        response = await client.post(
            f"/api/v1/people/{person_id}/activities?workspace_id={workspace_id}",
            json={"action_type": action_type, "source": source},
            headers=mock_headers,
        )
        assert response.status_code == 201

    combined_response = await client.get(
        f"/api/v1/people/{person_id}/activities",
        params={
            "workspace_id": workspace_id,
            "action_type": "message_sent",
            "source": "web_app",
        },
        headers=mock_headers,
    )
    assert combined_response.status_code == 200
    assert [item["action_type"] for item in combined_response.json()] == ["message_sent"]

    source_response = await client.get(
        f"/api/v1/people/{person_id}/activities",
        params={"workspace_id": workspace_id, "source": "web_app"},
        headers=mock_headers,
    )
    assert len(source_response.json()) == 2

    future_response = await client.get(
        f"/api/v1/people/{person_id}/activities",
        params={
            "workspace_id": workspace_id,
            "created_from": str(date.today() + timedelta(days=1)),
        },
        headers=mock_headers,
    )
    assert future_response.status_code == 200
    assert future_response.json() == []
