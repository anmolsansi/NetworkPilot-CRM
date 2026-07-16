import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_outreach_funnel_uses_durable_cumulative_events(
    client: AsyncClient,
    mock_headers: dict,
):
    workspace = await client.post(
        "/api/v1/workspaces", json={"name": "Funnel"}, headers=mock_headers
    )
    assert workspace.status_code == 201
    workspace_id = workspace.json()["id"]

    person_ids = []
    for index in range(5):
        response = await client.post(
            f"/api/v1/people?workspace_id={workspace_id}",
            json={
                "name": f"Funnel Person {index}",
                "linkedin_url": f"https://linkedin.com/in/{uuid.uuid4()}",
            },
            headers=mock_headers,
        )
        assert response.status_code == 201
        person_ids.append(response.json()["id"])

    sequences = [
        ["invite_sent"],
        ["invite_sent", "accepted"],
        ["invite_sent", "accepted", "message_sent"],
        ["invite_sent", "accepted", "message_sent", "reply_received"],
    ]
    for person_id, actions in zip(person_ids[1:], sequences, strict=True):
        for action in actions:
            response = await client.post(
                "/api/v1/extension/quick-action",
                json={
                    "workspace_id": workspace_id,
                    "person_id": person_id,
                    "action_type": action,
                },
                headers=mock_headers,
            )
            assert response.status_code == 200, response.text

    response = await client.get(
        f"/api/v1/workspaces/{workspace_id}/analytics/funnel",
        headers=mock_headers,
    )
    assert response.status_code == 200
    stages = {stage["key"]: stage for stage in response.json()["stages"]}
    assert [stage["key"] for stage in response.json()["stages"]] == [
        "saved",
        "invite_sent",
        "accepted",
        "messaged",
        "replied",
    ]
    assert {key: stage["count"] for key, stage in stages.items()} == {
        "saved": 5,
        "invite_sent": 4,
        "accepted": 3,
        "messaged": 2,
        "replied": 1,
    }
    assert stages["accepted"]["conversion_from_previous"] == 75.0
    assert stages["accepted"]["conversion_from_saved"] == 60.0
    assert stages["replied"]["conversion_from_previous"] == 50.0
    assert stages["replied"]["conversion_from_saved"] == 20.0
