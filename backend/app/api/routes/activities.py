import logging
import uuid

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.logging import get_logger, mask_id
from app.models.user import AppUser
from app.schemas.activities import (
    ActivityCreate,
    ActivityResponse,
    ActivityUpdate,
    AttachmentDownloadResponse,
    AttachmentResponse,
)
from app.services.activity_service import ActivityService
from app.services.storage_service import DOWNLOAD_URL_TTL_SECONDS, StorageService
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
    activity = await service.get_attachment_activity(workspace_id, activity_id)
    if activity.attachments:
        storage_service = StorageService()
        for attachment in activity.attachments:
            await storage_service.delete_file(attachment.storage_path)
        for attachment in activity.attachments:
            await db.delete(attachment)
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
    service = ActivityService(db)
    await service.get_attachment_activity(workspace_id, activity_id)

    storage_service = StorageService()
    stored_file = await storage_service.save_file(workspace_id, activity_id, file)
    try:
        return await service.add_attachment(
            workspace_id=workspace_id,
            activity_id=activity_id,
            file_name=file.filename or "unknown",
            file_size=stored_file.file_size,
            content_type=stored_file.content_type,
            storage_path=stored_file.object_key,
        )
    except Exception:
        await storage_service.delete_file(stored_file.object_key)
        raise


@router.get(
    "/attachments/{attachment_id}/download-url",
    response_model=AttachmentDownloadResponse,
)
async def get_attachment_download_url(
    attachment_id: uuid.UUID,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
) -> AttachmentDownloadResponse:
    """Authorize access and return a short-lived private download URL."""
    attachment = await ActivityService(db).get_attachment(workspace_id, attachment_id)
    url = StorageService().create_download_url(attachment.storage_path)
    return AttachmentDownloadResponse(url=url, expires_in=DOWNLOAD_URL_TTL_SECONDS)


@router.delete("/attachments/{attachment_id}", status_code=204)
async def delete_attachment(
    attachment_id: uuid.UUID,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Delete a private object and its attachment record."""
    service = ActivityService(db)
    attachment = await service.get_attachment(workspace_id, attachment_id)
    await StorageService().delete_file(attachment.storage_path)
    await service.delete_attachment(workspace_id, attachment_id)
    return Response(status_code=204)
