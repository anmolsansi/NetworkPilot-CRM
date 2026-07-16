import pytest
from httpx import AsyncClient

PERSON_ID = "00000000-0000-4000-8000-000000000001"


VERSION_ENDPOINTS = [
    ("v0.0.11", f"/api/v1/people/{PERSON_ID}/activities?workspace_id={{workspace_id}}"),
    ("v0.0.12", "/api/v1/tasks?workspace_id={workspace_id}"),
    ("v0.0.13", "/api/v1/people?workspace_id={workspace_id}&owner_id=me"),
    ("v0.0.14", "/api/v1/imports?workspace_id={workspace_id}"),
    ("v0.0.15", "/api/v1/people?workspace_id={workspace_id}&search=release"),
    ("v0.0.16", f"/api/v1/people/{PERSON_ID}/activities?workspace_id={{workspace_id}}"),
    ("v0.0.17", "/api/v1/people?workspace_id={workspace_id}"),
    ("v0.0.18", "/api/v1/workspaces/{workspace_id}/analytics/funnel"),
    ("v0.0.19", "/api/v1/workspaces/{workspace_id}/analytics/performance"),
    ("v0.0.20", "/api/v1/workspaces/{workspace_id}/members/me"),
    ("v0.0.21", "/api/v1/workspaces/{workspace_id}/analytics/goals"),
    ("v0.0.22", "/api/v1/workspaces/{workspace_id}/analytics/export.csv"),
    ("v0.0.23", "/api/v1/workspaces/{workspace_id}/invites"),
]

TENANT_CASES = [
    pytest.param(
        version,
        endpoint,
        marks=(
            pytest.mark.xfail(
                reason="workspace authorization fix is isolated in PR #61",
                strict=False,
            )
            if version in {"v0.0.18", "v0.0.19", "v0.0.21", "v0.0.22"}
            else []
        ),
        id=version,
    )
    for version, endpoint in VERSION_ENDPOINTS
]
TENANT_CASES[-1] = pytest.param(
    "v0.0.23",
    "/api/v1/workspaces/{workspace_id}/invites",
    marks=pytest.mark.xfail(
        reason="owner-only invitation authorization fix is isolated in PR #62",
        strict=False,
    ),
    id="v0.0.23",
)


async def create_workspace(client: AsyncClient, headers: dict, version: str) -> str:
    response = await client.post(
        "/api/v1/workspaces",
        json={"name": f"Release boundary {version}"},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("version", "endpoint"),
    VERSION_ENDPOINTS,
    ids=[version for version, _endpoint in VERSION_ENDPOINTS],
)
async def test_version_endpoint_rejects_unauthenticated_requests(
    client: AsyncClient,
    mock_headers: dict,
    version: str,
    endpoint: str,
):
    workspace_id = await create_workspace(client, mock_headers, version)

    response = await client.get(endpoint.format(workspace_id=workspace_id))

    assert response.status_code == 401


@pytest.mark.anyio
@pytest.mark.parametrize(("version", "endpoint"), TENANT_CASES)
async def test_version_endpoint_rejects_cross_workspace_requests(
    client: AsyncClient,
    mock_headers: dict,
    version: str,
    endpoint: str,
):
    workspace_id = await create_workspace(client, mock_headers, version)
    outsider_headers = {"Authorization": "Bearer release-outsider:outsider@example.test"}

    response = await client.get(
        endpoint.format(workspace_id=workspace_id),
        headers=outsider_headers,
    )

    assert response.status_code in {403, 404}
