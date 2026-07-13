from __future__ import annotations

import logging
import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError, ValidationError
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

    async def create(self, workspace_id: uuid.UUID, data: PipelineStageCreate) -> PipelineStage:
        """Create a new pipeline stage."""
        payload = data.model_dump(mode="json")
        await self._validate_configuration(workspace_id, payload)
        stage = PipelineStage(
            workspace_id=workspace_id,
            **payload,
        )
        self.db.add(stage)
        await self.db.flush()
        return await self.get(workspace_id, stage.id)

    async def update(
        self, workspace_id: uuid.UUID, stage_id: uuid.UUID, data: PipelineStageUpdate
    ) -> PipelineStage:
        """Update a pipeline stage."""
        stage = await self.get(workspace_id, stage_id)

        update_data = data.model_dump(exclude_unset=True, mode="json")
        await self._validate_configuration(workspace_id, update_data, current=stage)
        for field, value in update_data.items():
            setattr(stage, field, value)

        await self.db.flush()
        return await self.get(workspace_id, stage.id)

    async def delete(self, workspace_id: uuid.UUID, stage_id: uuid.UUID) -> None:
        """Delete a pipeline stage."""
        stage = await self.get(workspace_id, stage_id)
        await self.db.delete(stage)
        await self.db.flush()

    async def reorder(
        self, workspace_id: uuid.UUID, stage_ids: list[uuid.UUID]
    ) -> list[PipelineStage]:
        stages = list(await self.list(workspace_id))
        stages_by_id = {stage.id: stage for stage in stages}
        if set(stages_by_id) != set(stage_ids):
            raise ValidationError("Reorder must include every pipeline stage exactly once.")
        for index, stage in enumerate(stages):
            stage.order = 10000 + index
        await self.db.flush()
        for index, stage_id in enumerate(stage_ids):
            stages_by_id[stage_id].order = index
        await self.db.flush()
        return [stages_by_id[stage_id] for stage_id in stage_ids]

    async def _validate_configuration(
        self,
        workspace_id: uuid.UUID,
        values: dict,
        current: PipelineStage | None = None,
    ) -> None:
        if "name" in values:
            stmt = select(PipelineStage.id).where(
                PipelineStage.workspace_id == workspace_id,
                PipelineStage.name == values["name"],
            )
            if current:
                stmt = stmt.where(PipelineStage.id != current.id)
            if (await self.db.execute(stmt)).scalar_one_or_none() is not None:
                raise ConflictError("A pipeline stage with this name already exists")
        if "order" in values:
            stmt = select(PipelineStage.id).where(
                PipelineStage.workspace_id == workspace_id,
                PipelineStage.order == values["order"],
            )
            if current:
                stmt = stmt.where(PipelineStage.id != current.id)
            if (await self.db.execute(stmt)).scalar_one_or_none() is not None:
                raise ConflictError("A pipeline stage already uses this order")
        transition_ids = values.get("allowed_next_stage_ids")
        if transition_ids is not None:
            if len(transition_ids) != len(set(transition_ids)):
                raise ValidationError("Select each transition stage only once.")
            if current and str(current.id) in {str(item) for item in transition_ids}:
                raise ValidationError("A stage cannot transition to itself.")
            if transition_ids:
                transition_uuids = [uuid.UUID(str(stage_id)) for stage_id in transition_ids]
                result = await self.db.execute(
                    select(PipelineStage.id).where(
                        PipelineStage.workspace_id == workspace_id,
                        PipelineStage.id.in_(transition_uuids),
                    )
                )
                if len(result.scalars().all()) != len(transition_ids):
                    raise ValidationError(
                        "One or more transition stages do not belong to this workspace."
                    )
