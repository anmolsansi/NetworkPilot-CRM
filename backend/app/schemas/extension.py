import uuid
from datetime import date

from pydantic import BaseModel, Field


class ExtensionLookupRequest(BaseModel):
    linkedin_url: str = Field(..., min_length=1)
    workspace_id: uuid.UUID


class ExtensionLookupResponse(BaseModel):
    found: bool
    person_id: uuid.UUID | None = None
    name: str | None = None
    linkedin_url: str | None = None
    linkedin_slug: str | None = None
    stage: str | None = None
    priority: str | None = None
    next_action_type: str | None = None
    next_action_date: date | None = None
    last_action_type: str | None = None


class ExtensionQuickCreateRequest(BaseModel):
    linkedin_url: str = Field(..., min_length=1)
    workspace_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=200)
    role: str | None = Field(None, max_length=200)
    company: str | None = Field(None, max_length=200)
    location: str | None = Field(None, max_length=200)
    priority: str = Field(default="B", pattern=r"^[ABC]$")
    connection_note: str | None = None
    initial_action: str = Field(..., min_length=1)
    notes: str | None = None


class ExtensionQuickCreateResponse(BaseModel):
    person_id: uuid.UUID
    name: str
    linkedin_url: str
    stage: str
    next_action_type: str | None
    next_action_date: date | None
    activity_id: uuid.UUID


class ExtensionQuickActionRequest(BaseModel):
    person_id: uuid.UUID
    workspace_id: uuid.UUID
    action_type: str = Field(..., min_length=1)
    notes: str | None = None
    next_action_date: date | None = None
    next_action_type: str | None = None


class ExtensionQuickActionResponse(BaseModel):
    person_id: uuid.UUID
    stage: str
    next_action_type: str | None
    next_action_date: date | None
    activity_id: uuid.UUID
