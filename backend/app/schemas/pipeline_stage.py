import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PipelineStageBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    order: int = Field(0, ge=0, le=1000)
    color: str | None = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    allowed_next_stage_ids: list[uuid.UUID] = Field(default_factory=list, max_length=50)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Stage name cannot be blank.")
        return value


class PipelineStageCreate(PipelineStageBase):
    pass


class PipelineStageUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    order: int | None = Field(None, ge=0, le=1000)
    color: str | None = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    allowed_next_stage_ids: list[uuid.UUID] | None = Field(None, max_length=50)

    _normalize_name = field_validator("name")(PipelineStageBase.normalize_name.__func__)


class PipelineStageResponse(PipelineStageBase):
    id: uuid.UUID
    workspace_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PipelineStageReorder(BaseModel):
    stage_ids: list[uuid.UUID] = Field(..., min_length=1, max_length=100)

    @field_validator("stage_ids")
    @classmethod
    def unique_stage_ids(cls, value: list[uuid.UUID]) -> list[uuid.UUID]:
        if len(value) != len(set(value)):
            raise ValueError("Select each stage only once.")
        return value
