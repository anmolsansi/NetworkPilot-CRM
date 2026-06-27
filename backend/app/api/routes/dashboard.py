import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.dashboard import DashboardSummary, DuePersonCard
from app.services.dashboard_service import DashboardService
from app.services.workspace_service import require_workspace_access

router = APIRouter()


@router.get("/dashboard/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard summary counts."""
    service = DashboardService(db)
    return await service.get_summary(workspace_id)


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
    service = DashboardService(db)
    return await service.get_due(
        workspace_id=workspace_id,
        target_date=date,
        include_overdue=include_overdue,
        priority=priority,
    )
