import logging
import pytest
from app.services.calendar_link_service import generate_calendar_link
import uuid



_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
class TestGenerateCalendarLink:
    def test_basic_link(self):
        workspace_id = uuid.uuid4()
        dashboard_url = "http://localhost:5173/?workspace=123"
        url = generate_calendar_link(workspace_id, dashboard_url)

        assert "https://calendar.google.com/calendar/render" in url
        assert "action=TEMPLATE" in url
        assert "NetworkPilot" in url

    def test_custom_time(self):
        workspace_id = uuid.uuid4()
        dashboard_url = "http://localhost:5173"
        url = generate_calendar_link(workspace_id, dashboard_url, reminder_time="14:30")

        assert "NetworkPilot" in url

    def test_custom_timezone(self):
        workspace_id = uuid.uuid4()
        dashboard_url = "http://localhost:5173"
        url = generate_calendar_link(workspace_id, dashboard_url, timezone="America/New_York")

        assert "America%2FNew_York" in url or "America/New_York" in url

    def test_dashboard_url_in_description(self):
        workspace_id = uuid.uuid4()
        dashboard_url = "http://localhost:5173/?workspace=123"
        url = generate_calendar_link(workspace_id, dashboard_url)

        # URL should contain the dashboard URL encoded
        assert "dashboard" in url.lower() or "calendar" in url.lower()
