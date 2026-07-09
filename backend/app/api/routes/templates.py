import logging
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.logging import get_logger, mask_id
from app.schemas.templates import TemplateCreate, TemplateResponse, TemplateUpdate
from app.services.template_service import TemplateService
from app.services.workspace_service import require_workspace_access

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=list[TemplateResponse])
async def list_templates(
    workspace_id: uuid.UUID = Query(...),
    category: str | None = Query(None),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """List templates in workspace."""
    logger.info(
        "templates.list.started workspace_id=%s category=%s",
        mask_id(str(workspace_id)),
        category,
    )
    service = TemplateService(db)
    templates = await service.list(workspace_id, category)
    logger.info(
        "templates.list.completed workspace_id=%s count=%s",
        mask_id(str(workspace_id)),
        len(templates),
    )
    return templates


@router.post("", response_model=TemplateResponse, status_code=201)
async def create_template(
    data: TemplateCreate,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Create a template."""
    logger.info(
        "templates.create.started workspace_id=%s category=%s name_length=%s",
        mask_id(str(workspace_id)),
        data.category,
        len(data.name),
    )
    service = TemplateService(db)
    template = await service.create(workspace_id, data)
    logger.info(
        "templates.create.completed workspace_id=%s template_id=%s",
        mask_id(str(workspace_id)),
        mask_id(str(template.id)),
    )
    return template


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: uuid.UUID,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Get a template by ID."""
    logger.info(
        "templates.get.started workspace_id=%s template_id=%s",
        mask_id(str(workspace_id)),
        mask_id(str(template_id)),
    )
    service = TemplateService(db)
    template = await service.get(workspace_id, template_id)
    logger.info(
        "templates.get.completed workspace_id=%s template_id=%s",
        mask_id(str(workspace_id)),
        mask_id(str(template.id)),
    )
    return template


@router.patch("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: uuid.UUID,
    data: TemplateUpdate,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Update a template."""
    logger.info(
        "templates.update.started workspace_id=%s template_id=%s fields=%s",
        mask_id(str(workspace_id)),
        mask_id(str(template_id)),
        sorted(data.model_dump(exclude_unset=True).keys()),
    )
    service = TemplateService(db)
    template = await service.update(workspace_id, template_id, data)
    logger.info(
        "templates.update.completed workspace_id=%s template_id=%s",
        mask_id(str(workspace_id)),
        mask_id(str(template.id)),
    )
    return template


@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: uuid.UUID,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a template."""
    logger.info(
        "templates.delete.started workspace_id=%s template_id=%s",
        mask_id(str(workspace_id)),
        mask_id(str(template_id)),
    )
    service = TemplateService(db)
    await service.delete(workspace_id, template_id)
    logger.info(
        "templates.delete.completed workspace_id=%s template_id=%s",
        mask_id(str(workspace_id)),
        mask_id(str(template_id)),
    )
