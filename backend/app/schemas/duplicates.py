import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

MERGEABLE_PERSON_FIELDS = {
    "name",
    "first_name",
    "last_name",
    "role",
    "company",
    "location",
    "email",
    "phone_number",
    "premium",
    "company_website",
    "is_favorite",
    "favorite_notes",
    "priority",
    "connection_note",
    "notes",
    "next_action_type",
    "next_action_date",
}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DuplicateGroup(BaseModel):
    group_id: str
    people: list[dict[str, Any]]


class DuplicateMergeRequest(StrictModel):
    target_person_id: uuid.UUID
    source_person_id: uuid.UUID
    fields_to_keep_from_source: list[str] = Field(default_factory=list)

    @classmethod
    def _validate_fields(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("Select each merge field only once.")
        unknown = set(values) - MERGEABLE_PERSON_FIELDS
        if unknown:
            raise ValueError(f"Unsupported merge field: {sorted(unknown)[0]}")
        return values

    _fields_are_safe = field_validator("fields_to_keep_from_source")(_validate_fields)


class DuplicateMergeResponse(BaseModel):
    status: str = "success"
    target_person: dict[str, Any]
