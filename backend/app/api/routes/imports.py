import logging
import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.logging import get_logger, mask_id
from app.models.user import AppUser
from app.schemas.imports import ImportCommitRequest, ImportCommitResponse, ImportPreviewResponse
from app.services.csv_import_service import CsvImportService
from app.services.workspace_service import require_workspace_access

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
router = APIRouter()
logger = get_logger(__name__)


@router.post("/people/preview", response_model=ImportPreviewResponse)
async def preview_people_import(
    workspace_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    default_initial_action_type: str = Form("invite_sent"),
    duplicate_strategy: str = Form("skip"),
    default_priority: str = Form("B"),
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    logger.info(
        "imports.preview.started workspace_id=%s user_id=%s filename=%s duplicate_strategy=%s",
        mask_id(str(workspace_id)),
        mask_id(str(user.id)),
        file.filename,
        duplicate_strategy,
    )
    await require_workspace_access(workspace_id, user, db)
    content = await file.read()
    service = CsvImportService(db)
    preview = await service.preview(
        workspace_id=workspace_id,
        actor_user_id=user.id,
        content=content,
        file_name=file.filename,
        default_initial_action_type=default_initial_action_type,
        duplicate_strategy=duplicate_strategy,
        default_priority=default_priority,
    )
    logger.info(
        "imports.preview.completed workspace_id=%s import_batch_id=%s total=%s valid=%s invalid=%s",
        mask_id(str(workspace_id)),
        mask_id(str(preview.import_batch_id)),
        preview.summary.total_rows,
        preview.summary.valid_rows,
        preview.summary.invalid_rows,
    )
    return preview


@router.post("/people/commit", response_model=ImportCommitResponse)
async def commit_people_import(
    data: ImportCommitRequest,
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    logger.info(
        "imports.commit.started workspace_id=%s user_id=%s rows=%s import_batch_id=%s",
        mask_id(str(data.workspace_id)),
        mask_id(str(user.id)),
        len(data.rows),
        mask_id(str(data.import_batch_id)) if data.import_batch_id else None,
    )
    await require_workspace_access(data.workspace_id, user, db)
    service = CsvImportService(db)
    result = await service.commit(user.id, data)
    logger.info(
        "imports.commit.completed workspace_id=%s created=%s failed=%s skipped=%s",
        mask_id(str(data.workspace_id)),
        result["summary"]["created_count"],
        result["summary"]["failed_count"],
        result["summary"]["skipped_duplicates"],
    )
    return result
