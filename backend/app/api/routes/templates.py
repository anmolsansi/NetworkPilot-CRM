import uuid
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.templates import TemplateCreate, TemplateResponse, TemplateUpdate
from app.services.template_service import TemplateService
from app.services.workspace_service import require_workspace_access

router = APIRouter()


@router.get("", response_model=list[TemplateResponse])
async def list_templates(
    workspace_id: uuid.UUID = Query(...),
    category: str | None = Query(None),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """List templates in workspace."""
    service = TemplateService(db)
    return await service.list(workspace_id, category)


@router.post("", response_model=TemplateResponse, status_code=201)
async def create_template(
    data: TemplateCreate,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Create a template."""
    service = TemplateService(db)
    return await service.create(workspace_id, data)


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: uuid.UUID,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Get a template by ID."""
    service = TemplateService(db)
    return await service.get(workspace_id, template_id)


@router.patch("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: uuid.UUID,
    data: TemplateUpdate,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Update a template."""
    service = TemplateService(db)
    return await service.update(workspace_id, template_id, data)


@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: uuid.UUID,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a template."""
    service = TemplateService(db)
    await service.delete(workspace_id, template_id)
