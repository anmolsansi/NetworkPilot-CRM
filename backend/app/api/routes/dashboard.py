import logging
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.logging import get_logger, mask_id
from app.schemas.dashboard import DashboardSummary, DuePersonCard
from app.services.dashboard_service import DashboardService
from app.services.workspace_service import require_workspace_access

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
router = APIRouter()
logger = get_logger(__name__)


@router.get("/dashboard/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard summary counts."""
    logger.info("dashboard.summary.started workspace_id=%s", mask_id(str(workspace_id)))
    service = DashboardService(db)
    summary = await service.get_summary(workspace_id)
    logger.info(
        "dashboard.summary.completed workspace_id=%s due_today=%s overdue=%s active_total=%s",
        mask_id(str(workspace_id)),
        summary.due_today,
        summary.overdue,
        summary.active_total,
    )
    return summary


@router.get("/dashboard/due", response_model=list[DuePersonCard])
async def get_dashboard_due(
    workspace_id: uuid.UUID = Query(...),
    date: date | None = Query(None, alias="date"),
    include_overdue: bool = Query(True),
    priority: str | None = Query(None),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Get people due for follow-up."""
    logger.info(
        "dashboard.due.started workspace_id=%s date=%s include_overdue=%s priority=%s",
        mask_id(str(workspace_id)),
        date,
        include_overdue,
        priority,
    )
    service = DashboardService(db)
    due_people = await service.get_due(
        workspace_id=workspace_id,
        target_date=date,
        include_overdue=include_overdue,
        priority=priority,
    )
    logger.info(
        "dashboard.due.completed workspace_id=%s count=%s",
        mask_id(str(workspace_id)),
        len(due_people),
    )
    return due_people
