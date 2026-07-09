import logging
import uuid
from datetime import datetime

from pydantic import BaseModel

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
class WorkspaceMembershipResponse(BaseModel):
    workspace_id: uuid.UUID
    role: str
    created_at: datetime


class UserResponse(BaseModel):
    id: uuid.UUID
    supabase_user_id: uuid.UUID
    email: str
    display_name: str | None
    created_at: datetime
    updated_at: datetime
    workspaces: list[WorkspaceMembershipResponse] = []
