import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class PersonCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    linkedin_url: str = Field(..., min_length=1)
    role: str | None = Field(None, max_length=200)
    company: str | None = Field(None, max_length=200)
    location: str | None = Field(None, max_length=200)
    priority: str = Field(default="B", pattern=r"^[ABC]$")
    connection_note: str | None = None
    notes: str | None = None
    tags: list[str] | None = Field(None, max_length=20)


class PersonUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    role: str | None = Field(None, max_length=200)
    company: str | None = Field(None, max_length=200)
    location: str | None = Field(None, max_length=200)
    priority: str | None = Field(None, pattern=r"^[ABC]$")
    notes: str | None = None
    tags: list[str] | None = Field(None, max_length=20)


class PersonResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    linkedin_url: str
    linkedin_slug: str
    role: str | None
    company: str | None
    location: str | None
    priority: str
    stage: str
    status: str
    next_action_type: str | None
    next_action_date: date | None
    last_action_type: str | None
    last_action_date: date | None
    connection_note: str | None
    notes: str | None
    tags: list[str] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PersonListResponse(BaseModel):
    items: list[PersonResponse]
    total: int
    page: int
    limit: int


class SnoozeRequest(BaseModel):
    until_date: date = Field(..., description="Date to snooze until")
    notes: str | None = None


class ArchiveRequest(BaseModel):
    notes: str | None = None
