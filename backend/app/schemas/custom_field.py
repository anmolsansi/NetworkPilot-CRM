import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class CustomFieldBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    field_type: Literal["text", "number", "date", "boolean", "select"]
    options: dict[str, list[str]] | None = None

    @model_validator(mode="after")
    def validate_options(self):
        if self.field_type == "select":
            choices = (self.options or {}).get("choices", [])
            if not choices or len(choices) > 50 or len(choices) != len(set(choices)):
                raise ValueError("Select fields need 1 to 50 unique choices.")
        elif self.options is not None:
            raise ValueError("Only select fields can define choices.")
        return self


class CustomFieldCreate(CustomFieldBase):
    pass


class CustomFieldUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    options: dict[str, list[str]] | None = None


class CustomFieldResponse(CustomFieldBase):
    id: uuid.UUID
    workspace_id: uuid.UUID
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
