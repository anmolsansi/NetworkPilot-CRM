import logging
import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)


class TransitionResult(BaseModel):
    new_stage: str
    next_action_type: str | None
    next_action_date: date | None


class ActivityCreate(BaseModel):
    action_type: str = Field(..., min_length=1, max_length=50)
    source: str = Field(..., pattern=r"^(web_app|chrome_extension|system|csv_import)$")
    message: str | None = Field(None, max_length=5000)
    notes: str | None = Field(None, max_length=5000)
    next_action_date: date | None = None
    next_action_type: str | None = None
    template_id: uuid.UUID | None = None


class ActivityUpdate(BaseModel):
    is_pinned: bool | None = None
    message: str | None = Field(None, max_length=5000)
    notes: str | None = Field(None, max_length=5000)


class AttachmentResponse(BaseModel):
    id: uuid.UUID
    activity_id: uuid.UUID
    file_name: str
    file_size: int
    content_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ActivityResponse(BaseModel):
    id: uuid.UUID
    person_id: uuid.UUID
    workspace_id: uuid.UUID
    actor_user_id: uuid.UUID
    action_type: str
    source: str
    previous_stage: str | None
    new_stage: str | None
    message: str | None
    notes: str | None
    is_pinned: bool
    created_at: datetime
    template_id: uuid.UUID | None = None
    attachments: list[AttachmentResponse] = []

    model_config = {"from_attributes": True}
