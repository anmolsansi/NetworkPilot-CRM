import uuid
from datetime import date
from typing import Sequence

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import AppUser
from app.schemas.analytics import FunnelMetrics, PerformanceBreakdown, WeeklyGoalProgress
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/workspaces/{workspace_id}/analytics/funnel", response_model=FunnelMetrics)
async def get_funnel_metrics(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
) -> FunnelMetrics:
    """Get funnel metrics for a workspace."""
    service = AnalyticsService(db)
    return await service.get_funnel_metrics(workspace_id)


@router.get(
    "/workspaces/{workspace_id}/analytics/performance",
    response_model=list[PerformanceBreakdown],
)
async def get_template_performance(
    workspace_id: uuid.UUID,
    group_by: str = Query("template", pattern="^(template|stage|company|position|week)$"),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    attribution_days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
) -> Sequence[PerformanceBreakdown]:
    """Get attributed follow-up performance grouped by the selected dimension."""
    service = AnalyticsService(db)
    return await service.get_template_performance(
        workspace_id,
        group_by=group_by,
        date_from=date_from,
        date_to=date_to,
        attribution_days=attribution_days,
    )


@router.get("/workspaces/{workspace_id}/analytics/goals", response_model=WeeklyGoalProgress)
async def get_weekly_goal_progress(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
) -> WeeklyGoalProgress:
    """Get weekly goal progress for the current user."""
    service = AnalyticsService(db)
    return await service.get_weekly_goal_progress(workspace_id, current_user.id)


@router.get("/workspaces/{workspace_id}/analytics/export.csv")
async def export_analytics(
    workspace_id: uuid.UUID,
    export_type: str = "funnel",
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
) -> Response:
    """Export analytics as CSV."""
    service = AnalyticsService(db)
    csv_content = await service.export_analytics_csv(workspace_id)
    return Response(content=csv_content, media_type="text/csv; charset=utf-8")
