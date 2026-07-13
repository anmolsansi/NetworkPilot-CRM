import uuid
from typing import Sequence

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.database import get_db
from app.api.dependencies.workspace import get_workspace
from app.models.user import AppUser
from app.models.workspace import Workspace
from app.schemas.custom_field import CustomFieldCreate, CustomFieldResponse, CustomFieldUpdate
from app.services.custom_field_service import CustomFieldService

router = APIRouter()

@router.get("/", response_model=list[CustomFieldResponse])
async def list_custom_fields(
    workspace: Workspace = Depends(get_workspace),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
) -> Sequence[CustomFieldResponse]:
    return await CustomFieldService.get_all_for_workspace(db, workspace.id)

@router.post("/", response_model=CustomFieldResponse)
async def create_custom_field(
    data: CustomFieldCreate,
    workspace: Workspace = Depends(get_workspace),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
) -> CustomFieldResponse:
    return await CustomFieldService.create(db, workspace.id, data)

@router.put("/{field_id}", response_model=CustomFieldResponse)
async def update_custom_field(
    field_id: uuid.UUID,
    data: CustomFieldUpdate,
    workspace: Workspace = Depends(get_workspace),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
) -> CustomFieldResponse:
    return await CustomFieldService.update(db, field_id, workspace.id, data)

@router.delete("/{field_id}")
async def delete_custom_field(
    field_id: uuid.UUID,
    workspace: Workspace = Depends(get_workspace),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    await CustomFieldService.delete(db, field_id, workspace.id)
    return {"status": "success"}
