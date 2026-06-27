import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import AppUser
from app.schemas.activities import ActivityCreate, ActivityResponse
from app.schemas.people import PersonResponse
from app.services.activity_service import ActivityService
from app.services.workspace_service import require_workspace_access

router = APIRouter()


@router.get("/people/{person_id}/activities", response_model=list[ActivityResponse])
async def list_activities(
    person_id: uuid.UUID,
    workspace_id: uuid.UUID = Query(...),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """List activities for a person."""
    service = ActivityService(db)
    activities = await service.list(workspace_id, person_id, limit, offset)
    return activities


@router.post(
    "/people/{person_id}/activities",
    response_model=ActivityResponse,
    status_code=201,
)
async def create_activity(
    person_id: uuid.UUID,
    data: ActivityCreate,
    workspace_id: uuid.UUID = Query(...),
    user: AppUser = Depends(get_current_user),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Create an activity for a person."""
    service = ActivityService(db)
    activity, _ = await service.create(
        workspace_id=workspace_id,
        person_id=person_id,
        actor_user_id=user.id,
        data=data,
    )
    return activity
