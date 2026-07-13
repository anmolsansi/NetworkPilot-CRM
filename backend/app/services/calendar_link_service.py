import logging
import uuid
from urllib.parse import quote

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)


def generate_calendar_link(
    workspace_id: uuid.UUID,
    dashboard_url: str,
    reminder_time: str = "09:00",
    timezone: str = "UTC",
) -> str:
    """
    Generate a Google Calendar URL for a daily reminder.

    This creates a URL that opens Google Calendar with a pre-filled event
    for the user to save as a recurring daily reminder.

    Args:
        workspace_id: The workspace ID
        dashboard_url: The dashboard URL to include in the event
        reminder_time: Time in HH:MM format
        timezone: Timezone string

    Returns:
        Google Calendar URL
    """
    title = "NetworkPilot CRM - Daily Follow-up Check"
    description = (
        f"Check your dashboard for due follow-ups:\\n\\n{dashboard_url}\\n\\n"
        f"Review who needs follow-up today and take action."
    )

    # Build Google Calendar URL
    base_url = "https://calendar.google.com/calendar/render"
    params = [
        "action=TEMPLATE",
        f"text={quote(title)}",
        f"details={quote(description)}",
        f"ctz={quote(timezone)}",
    ]

    return f"{base_url}?{'&'.join(params)}"
