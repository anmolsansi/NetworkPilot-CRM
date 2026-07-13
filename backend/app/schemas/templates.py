import logging
import uuid

from pydantic import BaseModel, Field

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)


class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., pattern=r"^(connection_request|first_message|follow_up)$")
    body: str = Field(..., min_length=1, max_length=5000)
    variables: list[str] | None = None


class TemplateUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    category: str | None = Field(None, pattern=r"^(connection_request|first_message|follow_up)$")
    body: str | None = Field(None, min_length=1, max_length=5000)
    variables: list[str] | None = None


class TemplateResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    category: str
    body: str
    variables: list[str] | None
    is_default: bool
    created_at: uuid.UUID | None = None
    updated_at: uuid.UUID | None = None

    model_config = {"from_attributes": True}
