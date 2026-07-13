import logging
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.errors import NotFoundError
from app.core.logging import get_logger, mask_id
from app.models.workspace import Workspace
from app.schemas.calendar import CalendarLinkResponse
from app.services.calendar_link_service import generate_calendar_link
from app.services.workspace_service import require_workspace_access

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
router = APIRouter()
logger = get_logger(__name__)


@router.get("/daily-reminder-link", response_model=CalendarLinkResponse)
async def get_daily_reminder_link(
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Generate a Google Calendar URL for daily follow-up reminder."""
    logger.info("calendar.daily_link.started workspace_id=%s", mask_id(str(workspace_id)))
    # Get workspace
    result = await db.execute(
        select(Workspace).where(
            Workspace.id == workspace_id,
            Workspace.deleted_at.is_(None),
        )
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        logger.warning(
            "calendar.daily_link.workspace_missing workspace_id=%s",
            mask_id(str(workspace_id)),
        )
        raise NotFoundError("Workspace", str(workspace_id))

    # Build dashboard URL
    dashboard_url = f"http://localhost:5173/?workspace={workspace_id}"

    # Generate calendar link
    reminder_time = workspace.daily_reminder_time.strftime("%H:%M")
    url = generate_calendar_link(
        workspace_id=workspace_id,
        dashboard_url=dashboard_url,
        reminder_time=reminder_time,
        timezone=workspace.timezone,
    )
    logger.info(
        "calendar.daily_link.completed workspace_id=%s timezone=%s reminder_time=%s",
        mask_id(str(workspace_id)),
        workspace.timezone,
        reminder_time,
    )

    return CalendarLinkResponse(
        url=url,
        title="NetworkPilot CRM - Daily Follow-up Check",
        description="Daily reminder to check your dashboard for due follow-ups.",
    )
