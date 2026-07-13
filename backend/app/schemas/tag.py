import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: str | None = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Tag name cannot be blank")
        return value


class TagCreate(TagBase):
    workspace_id: uuid.UUID


class TagUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50)
    color: str | None = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")

    _normalize_name = field_validator("name")(TagBase.normalize_name.__func__)


class TagResponse(TagBase):
    id: uuid.UUID
    workspace_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
