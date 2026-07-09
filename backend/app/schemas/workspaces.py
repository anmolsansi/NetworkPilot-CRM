import logging
import uuid
from datetime import datetime, time

from pydantic import BaseModel, Field

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    default_follow_up_delay_days: int = Field(default=3, ge=1, le=30)
    default_acceptance_check_delay_days: int = Field(default=1, ge=1, le=14)
    timezone: str = Field(default="UTC", max_length=50)


class WorkspaceUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    default_follow_up_delay_days: int | None = Field(None, ge=1, le=30)
    default_acceptance_check_delay_days: int | None = Field(None, ge=1, le=14)
    daily_reminder_time: str | None = Field(None, pattern=r"^\d{2}:\d{2}$")
    timezone: str | None = Field(None, max_length=50)


class WorkspaceResponse(BaseModel):
    id: uuid.UUID
    name: str
    owner_id: uuid.UUID
    default_follow_up_delay_days: int
    default_acceptance_check_delay_days: int
    daily_reminder_time: time
    timezone: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
