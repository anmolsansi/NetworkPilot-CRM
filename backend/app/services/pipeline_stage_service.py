import logging
import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.pipeline_stage import PipelineStage
from app.schemas.pipeline_stage import PipelineStageCreate, PipelineStageUpdate

logger = logging.getLogger(__name__)


class PipelineStageService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self, workspace_id: uuid.UUID) -> Sequence[PipelineStage]:
        """List all pipeline stages for a workspace."""
        result = await self.db.execute(
            select(PipelineStage)
            .where(PipelineStage.workspace_id == workspace_id)
            .order_by(PipelineStage.order.asc(), PipelineStage.created_at.asc())
        )
        return result.scalars().all()

    async def get(self, workspace_id: uuid.UUID, stage_id: uuid.UUID) -> PipelineStage:
        """Get a pipeline stage by ID."""
        result = await self.db.execute(
            select(PipelineStage).where(
                PipelineStage.id == stage_id,
                PipelineStage.workspace_id == workspace_id,
            )
        )
        stage = result.scalar_one_or_none()
        if not stage:
            raise NotFoundError("PipelineStage", str(stage_id))
        return stage

    async def create(
        self, workspace_id: uuid.UUID, data: PipelineStageCreate
    ) -> PipelineStage:
        """Create a new pipeline stage."""
        stage = PipelineStage(
            workspace_id=workspace_id,
            **data.model_dump(),
        )
        self.db.add(stage)
        await self.db.flush()
        return stage

    async def update(
        self, workspace_id: uuid.UUID, stage_id: uuid.UUID, data: PipelineStageUpdate
    ) -> PipelineStage:
        """Update a pipeline stage."""
        stage = await self.get(workspace_id, stage_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(stage, field, value)

        await self.db.flush()
        return stage

    async def delete(self, workspace_id: uuid.UUID, stage_id: uuid.UUID) -> None:
        """Delete a pipeline stage."""
        stage = await self.get(workspace_id, stage_id)
        await self.db.delete(stage)
        await self.db.flush()
