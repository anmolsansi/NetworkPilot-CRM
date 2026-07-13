import uuid
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.logging import get_logger, mask_id
from app.models.user import AppUser
from app.schemas.saved_views import SavedViewCreate, SavedViewResponse, SavedViewUpdate
from app.services.saved_views_service import SavedViewsService
from app.services.workspace_service import require_workspace_access

router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=List[SavedViewResponse])
async def list_saved_views(
    workspace_id: uuid.UUID = Query(...),
    user: AppUser = Depends(get_current_user),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """List saved views for the workspace and user."""
    logger.info(
        "saved_views.list.started workspace_id=%s user_id=%s",
        mask_id(str(workspace_id)),
        mask_id(str(user.id)),
    )
    service = SavedViewsService(db)
    views = await service.list(workspace_id, user.id)
    return views


@router.post("", response_model=SavedViewResponse, status_code=201)
async def create_saved_view(
    data: SavedViewCreate,
    workspace_id: uuid.UUID = Query(...),
    user: AppUser = Depends(get_current_user),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Create a new saved view."""
    logger.info(
        "saved_views.create.started workspace_id=%s user_id=%s",
        mask_id(str(workspace_id)),
        mask_id(str(user.id)),
    )
    service = SavedViewsService(db)
    view = await service.create(workspace_id, user.id, data)
    return view


@router.patch("/{view_id}", response_model=SavedViewResponse)
async def update_saved_view(
    view_id: uuid.UUID,
    data: SavedViewUpdate,
    workspace_id: uuid.UUID = Query(...),
    user: AppUser = Depends(get_current_user),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Update a saved view."""
    logger.info(
        "saved_views.update.started workspace_id=%s user_id=%s view_id=%s",
        mask_id(str(workspace_id)),
        mask_id(str(user.id)),
        mask_id(str(view_id)),
    )
    service = SavedViewsService(db)
    view = await service.update(workspace_id, user.id, view_id, data)
    return view


@router.delete("/{view_id}", status_code=204)
async def delete_saved_view(
    view_id: uuid.UUID,
    workspace_id: uuid.UUID = Query(...),
    user: AppUser = Depends(get_current_user),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Delete a saved view."""
    logger.info(
        "saved_views.delete.started workspace_id=%s user_id=%s view_id=%s",
        mask_id(str(workspace_id)),
        mask_id(str(user.id)),
        mask_id(str(view_id)),
    )
    service = SavedViewsService(db)
    await service.delete(workspace_id, user.id, view_id)
