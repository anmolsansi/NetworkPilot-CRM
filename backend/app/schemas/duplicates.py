import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class DuplicateGroup(BaseModel):
    group_id: str
    people: list[dict[str, Any]]

class DuplicateMergeRequest(StrictModel):
    target_person_id: uuid.UUID
    source_person_id: uuid.UUID
    fields_to_keep_from_source: list[str] = Field(default_factory=list)

class DuplicateMergeResponse(BaseModel):
    status: str = "success"
    target_person: dict[str, Any]
