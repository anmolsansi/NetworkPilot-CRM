import logging
import uuid
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.logging import get_logger, mask_id
from app.models.user import AppUser
from app.schemas.duplicates import DuplicateGroup, DuplicateMergeRequest, DuplicateMergeResponse
from app.services.duplicate_service import DuplicateService
from app.services.workspace_service import require_workspace_access

router = APIRouter()
logger = get_logger(__name__)

@router.get("", response_model=List[DuplicateGroup])
async def find_duplicates(
    workspace_id: uuid.UUID = Query(...),
    user: AppUser = Depends(get_current_user),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Find potential duplicate people in the workspace."""
    logger.info("duplicates.find.started workspace_id=%s user_id=%s", mask_id(str(workspace_id)), mask_id(str(user.id)))
    service = DuplicateService(db)
    groups = await service.find_duplicates(workspace_id)
    return groups

@router.post("/merge", response_model=DuplicateMergeResponse)
async def merge_people(
    data: DuplicateMergeRequest,
    workspace_id: uuid.UUID = Query(...),
    user: AppUser = Depends(get_current_user),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Merge two people records and reassign activities."""
    logger.info(
        "duplicates.merge.started workspace_id=%s user_id=%s target=%s source=%s",
        mask_id(str(workspace_id)),
        mask_id(str(user.id)),
        mask_id(str(data.target_person_id)),
        mask_id(str(data.source_person_id))
    )
    service = DuplicateService(db)
    target_person = await service.merge_people(
        workspace_id=workspace_id,
        user_id=user.id,
        target_person_id=data.target_person_id,
        source_person_id=data.source_person_id,
        fields_to_keep_from_source=data.fields_to_keep_from_source
    )
    return DuplicateMergeResponse(target_person=target_person)
