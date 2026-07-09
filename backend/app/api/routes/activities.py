import logging
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.logging import get_logger, mask_id
from app.models.user import AppUser
from app.schemas.activities import ActivityCreate, ActivityResponse
from app.services.activity_service import ActivityService
from app.services.workspace_service import require_workspace_access

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
router = APIRouter()
logger = get_logger(__name__)


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
    logger.info(
        "activities.list.started workspace_id=%s person_id=%s limit=%s offset=%s",
        mask_id(str(workspace_id)),
        mask_id(str(person_id)),
        limit,
        offset,
    )
    service = ActivityService(db)
    activities = await service.list(workspace_id, person_id, limit, offset)
    logger.info(
        "activities.list.completed workspace_id=%s person_id=%s count=%s",
        mask_id(str(workspace_id)),
        mask_id(str(person_id)),
        len(activities),
    )
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
    logger.info(
        "activities.create.started workspace_id=%s person_id=%s user_id=%s action_type=%s",
        mask_id(str(workspace_id)),
        mask_id(str(person_id)),
        mask_id(str(user.id)),
        data.action_type,
    )
    service = ActivityService(db)
    activity, _ = await service.create(
        workspace_id=workspace_id,
        person_id=person_id,
        actor_user_id=user.id,
        data=data,
    )
    logger.info(
        "activities.create.completed workspace_id=%s person_id=%s activity_id=%s",
        mask_id(str(workspace_id)),
        mask_id(str(person_id)),
        mask_id(str(activity.id)),
    )
    return activity
