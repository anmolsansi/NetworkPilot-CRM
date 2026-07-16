import logging
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

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
    id: uuid.UUID | None = None
    name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    linkedin_url: str | None = None
    normalized_profile_url: str | None = None
    errors: list[str] = Field(default_factory=list)
    current_role: str | None = None
    current_company: str | None = None
    location: str | None = None
    email: str | None = None
    phone_number: str | None = None
    premium: bool | None = None
    company_website: str | None = None
    processed_at: datetime | None = None
    processed_at_millis: int | None = None
    invite_accepted_at: datetime | None = None
    invite_accepted_at_millis: int | None = None
    priority: str | None = None
    connection_note: str | None = None
    conversation_context: str | None = None
    tags: list[str] = Field(default_factory=list)
    initial_action_type: str | None = None
    next_action_date: date | None = None


class ImportPreviewResponse(BaseModel):
    summary: ImportPreviewSummary
    rows: list[ImportPreviewRow]
    provided_headers: list[str] = Field(default_factory=list)
    import_batch_id: uuid.UUID | None = None


class ImportCommitRow(BaseModel):
    id: uuid.UUID | None = None
    name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    linkedin_url: str | None = None
    current_role: str | None = None
    current_company: str | None = None
    location: str | None = None
    email: str | None = None
    phone_number: str | None = None
    premium: bool | None = None
    company_website: str | None = None
    processed_at: datetime | None = None
    processed_at_millis: int | None = None
    invite_accepted_at: datetime | None = None
    invite_accepted_at_millis: int | None = None
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
    provided_headers: list[str] = Field(default_factory=list)
    rows: list[ImportCommitRow]
    import_batch_id: uuid.UUID | None = None
    chunk_index: int = Field(default=0, ge=0)
    total_chunks: int = Field(default=1, ge=1)


class ImportCreatedPerson(BaseModel):
    id: uuid.UUID
    name: str
    normalized_profile_url: str
    stage: str
    next_action_type: str | None
    next_action_date: date | None


class ImportJobResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    status: str
    file_name: str | None = None
    total_rows: int
    processed_rows: int
    failed_rows: int
    attempt_count: int
    started_at: datetime | None = None
    heartbeat_at: datetime | None = None
    error_log: list[dict] | None = None
    created_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
