import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.logging import get_logger, mask_id
from app.models.user import AppUser
from app.schemas.activities import (
    ActivityCreate,
    ActivityResponse,
    ActivityUpdate,
    AttachmentResponse,
)
from app.services.activity_service import ActivityService
from app.services.storage_service import StorageService
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
    action_type: str | None = Query(None, min_length=1, max_length=50),
    source: str | None = Query(None, pattern=r"^(web_app|chrome_extension|system|csv_import)$"),
    created_from: datetime | None = Query(None),
    created_to: datetime | None = Query(None),
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
    activities = await service.list(
        workspace_id,
        person_id,
        limit,
        offset,
        action_type=action_type,
        source=source,
        created_from=created_from,
        created_to=created_to,
    )
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


@router.patch("/activities/{activity_id}", response_model=ActivityResponse)
async def update_activity(
    activity_id: uuid.UUID,
    data: ActivityUpdate,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing activity."""
    service = ActivityService(db)
    return await service.update(
        workspace_id=workspace_id,
        activity_id=activity_id,
        is_pinned=data.is_pinned,
        message=data.message,
        notes=data.notes,
    )

@router.delete("/activities/{activity_id}", status_code=204)
async def delete_activity(
    activity_id: uuid.UUID,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete an activity."""
    service = ActivityService(db)
    await service.soft_delete(workspace_id=workspace_id, activity_id=activity_id)
    return Response(status_code=204)
@router.post("/activities/{activity_id}/attachments", response_model=AttachmentResponse)
async def upload_attachment(
    activity_id: uuid.UUID,
    file: UploadFile = File(...),
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Upload an attachment to an activity."""
    storage_service = StorageService()
    storage_path = await storage_service.save_file(workspace_id, file)

    file_size = 0
    if file.size is not None:
        file_size = file.size

    service = ActivityService(db)
    attachment = await service.add_attachment(
        workspace_id=workspace_id,
        activity_id=activity_id,
        file_name=file.filename or "unknown",
        file_size=file_size,
        content_type=file.content_type or "application/octet-stream",
        storage_path=storage_path,
    )
    return attachment
