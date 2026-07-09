import logging
import uuid
from datetime import date

from pydantic import BaseModel, Field

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
IMPORT_ACTION_TYPES = {
    "saved_for_later",
    "invite_sent",
    "already_connected",
    "accepted_no_message",
    "first_message_sent",
}


class ImportPreviewSummary(BaseModel):
    total_rows: int
    valid_rows: int
    duplicate_rows: int
    invalid_rows: int


class ImportPreviewRow(BaseModel):
    row_number: int
    status: str
    name: str | None = None
    linkedin_url: str | None = None
    normalized_profile_url: str | None = None
    errors: list[str] = Field(default_factory=list)
    current_role: str | None = None
    current_company: str | None = None
    location: str | None = None
    priority: str | None = None
    connection_note: str | None = None
    conversation_context: str | None = None
    tags: list[str] = Field(default_factory=list)
    initial_action_type: str | None = None
    next_action_date: date | None = None


class ImportPreviewResponse(BaseModel):
    summary: ImportPreviewSummary
    rows: list[ImportPreviewRow]
    import_batch_id: uuid.UUID | None = None


class ImportCommitRow(BaseModel):
    name: str
    linkedin_url: str
    current_role: str | None = None
    current_company: str | None = None
    location: str | None = None
    priority: str | None = None
    connection_note: str | None = None
    conversation_context: str | None = None
    tags: list[str] | str | None = None
    initial_action_type: str | None = None
    next_action_date: date | None = None


class ImportCommitRequest(BaseModel):
    workspace_id: uuid.UUID
    default_initial_action_type: str = Field(default="invite_sent")
    duplicate_strategy: str = Field(default="skip")
    default_priority: str = Field(default="B")
    rows: list[ImportCommitRow]
    import_batch_id: uuid.UUID | None = None


class ImportCreatedPerson(BaseModel):
    id: uuid.UUID
    name: str
    normalized_profile_url: str
    stage: str
    next_action_type: str | None
    next_action_date: date | None


class ImportCommitResponse(BaseModel):
    summary: dict[str, int]
    created_people: list[ImportCreatedPerson]
    errors: list[ImportPreviewRow]
