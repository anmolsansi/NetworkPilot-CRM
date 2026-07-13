import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PipelineStageBase(BaseModel):
    name: str
    order: int = 0
    color: str | None = None


class PipelineStageCreate(PipelineStageBase):
    pass


class PipelineStageUpdate(BaseModel):
    name: str | None = None
    order: int | None = None
    color: str | None = None


class PipelineStageResponse(PipelineStageBase):
    id: uuid.UUID
    workspace_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
