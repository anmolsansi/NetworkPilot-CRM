from httpx import AsyncClient


class TestPhase3Completion:
    async def _workspace(self, client: AsyncClient, headers: dict) -> str:
        response = await client.post(
            "/api/v1/workspaces",
            json={"name": "Phase 3 Workspace"},
            headers=headers,
        )
        assert response.status_code == 201
        return response.json()["id"]

    async def test_dashboard_config(self, client: AsyncClient, mock_headers: dict):
        workspace_id = await self._workspace(client, mock_headers)

        # Update settings via me endpoint
        update_resp = await client.patch(
            f"/api/v1/workspaces/{workspace_id}/members/me",
            json={
                "dashboard_config": {"widgets": ["funnel", "activity"]},
                "weekly_outreach_target": 75,
            },
            headers=mock_headers,
        )
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data["weekly_outreach_target"] == 75
        assert data["dashboard_config"]["version"] == 1
        assert [widget["id"] for widget in data["dashboard_config"]["widgets"][:2]] == [
            "summary",
            "due",
        ]

    async def test_analytics_funnel_and_performance(self, client: AsyncClient, mock_headers: dict):
        workspace_id = await self._workspace(client, mock_headers)

        # Test funnel
        funnel_resp = await client.get(
            f"/api/v1/workspaces/{workspace_id}/analytics/funnel", headers=mock_headers
        )
        assert funnel_resp.status_code == 200
        data = funnel_resp.json()
        assert [stage["key"] for stage in data["stages"]] == [
            "saved",
            "invite_sent",
            "accepted",
            "messaged",
            "replied",
        ]

        # Test performance
        perf_resp = await client.get(
            f"/api/v1/workspaces/{workspace_id}/analytics/performance", headers=mock_headers
        )
        assert perf_resp.status_code == 200
        data = perf_resp.json()
        assert isinstance(data, list)

    async def test_analytics_export(self, client: AsyncClient, mock_headers: dict):
        workspace_id = await self._workspace(client, mock_headers)

        export_resp = await client.get(
            f"/api/v1/workspaces/{workspace_id}/analytics/export.csv", headers=mock_headers
        )
        assert export_resp.status_code == 200
        assert export_resp.headers["content-type"] == "text/csv; charset=utf-8"
        content = export_resp.text
        assert "Metric,Count" in content

        pdf_resp = await client.get(
            f"/api/v1/workspaces/{workspace_id}/analytics/export.pdf",
            params={"date_from": "2026-01-01", "date_to": "2026-12-31"},
            headers=mock_headers,
        )
        assert pdf_resp.status_code == 200
        assert pdf_resp.headers["content-type"] == "application/pdf"
        assert "networkpilot-analytics.pdf" in pdf_resp.headers["content-disposition"]
        assert pdf_resp.content.startswith(b"%PDF")
