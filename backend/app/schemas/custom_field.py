import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class CustomFieldBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    field_type: str = Field(..., min_length=1, max_length=50) # text, number, date, boolean, select
    options: dict | None = None

class CustomFieldCreate(CustomFieldBase):
    pass

class CustomFieldUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    options: dict | None = None

class CustomFieldResponse(CustomFieldBase):
    id: uuid.UUID
    workspace_id: uuid.UUID
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
