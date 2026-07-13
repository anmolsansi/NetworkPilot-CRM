import logging
import uuid
from typing import List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.pipeline_stage import (
    PipelineStageCreate,
    PipelineStageReorder,
    PipelineStageResponse,
    PipelineStageUpdate,
)
from app.services.pipeline_stage_service import PipelineStageService
from app.services.workspace_service import require_workspace_access

logger = logging.getLogger(__name__)

router = APIRouter(tags=["pipeline_stages"])


@router.post("/reorder", response_model=List[PipelineStageResponse])
async def reorder_pipeline_stages(
    data: PipelineStageReorder,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    return await PipelineStageService(db).reorder(workspace_id, data.stage_ids)


@router.get("", response_model=List[PipelineStageResponse])
async def list_pipeline_stages(
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """List all pipeline stages in the workspace."""
    service = PipelineStageService(db)
    return await service.list(workspace_id)


@router.post("", response_model=PipelineStageResponse, status_code=status.HTTP_201_CREATED)
async def create_pipeline_stage(
    data: PipelineStageCreate,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Create a new pipeline stage."""
    service = PipelineStageService(db)
    return await service.create(workspace_id, data)


@router.get("/{stage_id}", response_model=PipelineStageResponse)
async def get_pipeline_stage(
    stage_id: uuid.UUID,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Get a pipeline stage by ID."""
    service = PipelineStageService(db)
    return await service.get(workspace_id, stage_id)


@router.patch("/{stage_id}", response_model=PipelineStageResponse)
async def update_pipeline_stage(
    stage_id: uuid.UUID,
    data: PipelineStageUpdate,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Update a pipeline stage."""
    service = PipelineStageService(db)
    return await service.update(workspace_id, stage_id, data)


@router.delete("/{stage_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pipeline_stage(
    stage_id: uuid.UUID,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Delete a pipeline stage."""
    service = PipelineStageService(db)
    await service.delete(workspace_id, stage_id)
