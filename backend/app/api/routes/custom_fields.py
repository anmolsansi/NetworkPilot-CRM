import uuid
from typing import Sequence

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.custom_field import CustomFieldCreate, CustomFieldResponse, CustomFieldUpdate
from app.services.custom_field_service import CustomFieldService
from app.services.workspace_service import require_workspace_access

router = APIRouter(tags=["custom_fields"])

@router.get("", response_model=list[CustomFieldResponse])
async def list_custom_fields(
    workspace_id: uuid.UUID = Query(...),
    _workspace=Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
) -> Sequence[CustomFieldResponse]:
    return await CustomFieldService.get_all_for_workspace(db, workspace_id)

@router.post("", response_model=CustomFieldResponse, status_code=status.HTTP_201_CREATED)
async def create_custom_field(
    data: CustomFieldCreate,
    workspace_id: uuid.UUID = Query(...),
    _workspace=Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
) -> CustomFieldResponse:
    return await CustomFieldService.create(db, workspace_id, data)

@router.put("/{field_id}", response_model=CustomFieldResponse)
async def update_custom_field(
    field_id: uuid.UUID,
    data: CustomFieldUpdate,
    workspace_id: uuid.UUID = Query(...),
    _workspace=Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
) -> CustomFieldResponse:
    return await CustomFieldService.update(db, field_id, workspace_id, data)

@router.delete("/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_field(
    field_id: uuid.UUID,
    workspace_id: uuid.UUID = Query(...),
    _workspace=Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
) -> None:
    await CustomFieldService.delete(db, field_id, workspace_id)
