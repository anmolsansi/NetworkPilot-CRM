import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

ALLOWED_FILTERS = {
    "search",
    "company",
    "role",
    "email",
    "location",
    "premium",
    "favorite",
    "favoriteNotes",
    "processedFrom",
    "processedTo",
    "stage",
    "priority",
    "deleted",
    "tagId",
}
ALLOWED_SORT_FIELDS = {
    "linkedin_url",
    "first_name",
    "last_name",
    "company",
    "role",
    "email",
    "phone_number",
    "premium",
    "location",
    "company_website",
    "processed_at",
    "processed_at_millis",
    "invite_accepted_at",
    "invite_accepted_at_millis",
    "created_at",
    "is_favorite",
    "favorite_notes",
}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SavedViewCreate(StrictModel):
    name: str = Field(..., min_length=1, max_length=100)
    filters: dict[str, Any]
    sort_by: str = Field(..., max_length=50)
    sort_order: str = Field(..., pattern="^(asc|desc)$")

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Saved view name cannot be blank.")
        return value

    @field_validator("filters")
    @classmethod
    def validate_filters(cls, value: dict[str, Any]) -> dict[str, Any]:
        unknown = set(value) - ALLOWED_FILTERS
        if unknown:
            raise ValueError(f"Unsupported saved filter: {sorted(unknown)[0]}")
        if any(isinstance(item, (dict, list)) for item in value.values()):
            raise ValueError("Saved filter values must be scalar.")
        return value

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, value: str) -> str:
        if value not in ALLOWED_SORT_FIELDS:
            raise ValueError("Unsupported saved sort field.")
        return value


class SavedViewUpdate(StrictModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    filters: dict[str, Any] | None = None
    sort_by: str | None = Field(None, max_length=50)
    sort_order: str | None = Field(None, pattern="^(asc|desc)$")

    _normalize_name = field_validator("name")(SavedViewCreate.normalize_name.__func__)
    _validate_filters = field_validator("filters")(SavedViewCreate.validate_filters.__func__)
    _validate_sort_by = field_validator("sort_by")(SavedViewCreate.validate_sort_by.__func__)


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
