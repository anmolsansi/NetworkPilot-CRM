import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class SavedViewCreate(StrictModel):
    name: str = Field(..., min_length=1, max_length=100)
    filters: dict[str, Any]
    sort_by: str = Field(..., max_length=50)
    sort_order: str = Field(..., max_length=4)

class SavedViewUpdate(StrictModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    filters: dict[str, Any] | None = None
    sort_by: str | None = Field(None, max_length=50)
    sort_order: str | None = Field(None, max_length=4)

class SavedViewResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    name: str
    filters: dict[str, Any]
    sort_by: str
    sort_order: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
