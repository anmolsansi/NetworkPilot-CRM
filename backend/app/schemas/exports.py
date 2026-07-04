import uuid
from datetime import date

from pydantic import BaseModel, Field


class PeopleExportFilters(BaseModel):
    workspace_id: uuid.UUID
    stage: str | None = None
    status: str | None = None
    priority: str | None = Field(default=None, pattern=r"^[ABC]$")
    next_action_type: str | None = None
    accepted_only: bool = False
    due: str = Field(default="all", pattern=r"^(all|today|overdue)$")
    date_from: date | None = None
    date_to: date | None = None
    tags: str | None = None
    company: str | None = None
    role: str | None = None
    include_private_notes: bool = False
