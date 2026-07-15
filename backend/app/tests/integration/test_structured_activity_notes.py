import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_structured_activity_notes_can_be_created_updated_and_cleared(
    client: AsyncClient,
    mock_headers: dict,
):
    workspace_response = await client.post(
        "/api/v1/workspaces",
        json={"name": "Structured Notes"},
        headers=mock_headers,
    )
    workspace_id = workspace_response.json()["id"]

    person_response = await client.post(
        f"/api/v1/people?workspace_id={workspace_id}",
        json={
            "name": "Grace Hopper",
            "linkedin_url": "https://linkedin.com/in/grace-structured-notes",
        },
        headers=mock_headers,
    )
    assert person_response.status_code == 201
    person_id = person_response.json()["id"]

    activity_response = await client.post(
        f"/api/v1/people/{person_id}/activities?workspace_id={workspace_id}",
        json={
            "action_type": "reply_received",
            "source": "web_app",
            "notes": "Detailed raw notes",
            "interaction_summary": "Discussed the platform roadmap",
            "outcome": "Agreed to a technical review",
            "next_steps": "Send architecture notes on Friday",
        },
        headers=mock_headers,
    )
    assert activity_response.status_code == 201
    activity = activity_response.json()
    assert activity["interaction_summary"] == "Discussed the platform roadmap"
    assert activity["outcome"] == "Agreed to a technical review"
    assert activity["next_steps"] == "Send architecture notes on Friday"

    update_response = await client.patch(
        f"/api/v1/activities/{activity['id']}?workspace_id={workspace_id}",
        json={"outcome": "Review scheduled", "next_steps": None},
        headers=mock_headers,
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["outcome"] == "Review scheduled"
    assert updated["next_steps"] is None
    assert updated["notes"] == "Detailed raw notes"
