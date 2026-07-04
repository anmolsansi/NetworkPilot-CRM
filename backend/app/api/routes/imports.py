import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import AppUser
from app.schemas.imports import ImportCommitRequest, ImportCommitResponse, ImportPreviewResponse
from app.services.csv_import_service import CsvImportService
from app.services.workspace_service import require_workspace_access

router = APIRouter()


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
    await require_workspace_access(workspace_id, user, db)
    content = await file.read()
    service = CsvImportService(db)
    return await service.preview(
        workspace_id=workspace_id,
        actor_user_id=user.id,
        content=content,
        file_name=file.filename,
        default_initial_action_type=default_initial_action_type,
        duplicate_strategy=duplicate_strategy,
        default_priority=default_priority,
    )


@router.post("/people/commit", response_model=ImportCommitResponse)
async def commit_people_import(
    data: ImportCommitRequest,
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_workspace_access(data.workspace_id, user, db)
    service = CsvImportService(db)
    return await service.commit(user.id, data)
