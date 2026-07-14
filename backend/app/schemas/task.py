import uuid
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    person_id: uuid.UUID
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    due_date: Optional[date] = None
    assigned_to: Optional[uuid.UUID] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    due_date: Optional[date] = None
    assigned_to: Optional[uuid.UUID] = None
    status: Optional[Literal["open", "completed"]] = None


class TaskResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    person_id: uuid.UUID
    person_name: str
    assigned_to: Optional[uuid.UUID]
    assignee_email: Optional[str]
    title: str
    description: Optional[str]
    due_date: Optional[date]
    status: str
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int
    page: int
    limit: int
