import uuid
from pydantic import BaseModel, ConfigDict

class TagBase(BaseModel):
    name: str
    color: str | None = None

class TagCreate(TagBase):
    workspace_id: uuid.UUID

class TagResponse(TagBase):
    id: uuid.UUID
    workspace_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
