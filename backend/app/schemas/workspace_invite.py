import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr


class WorkspaceInviteCreate(BaseModel):
    email: EmailStr
    role: Literal["member"] = "member"


class WorkspaceInviteResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    email: str
    role: str
    status: str
    invited_by_user_id: uuid.UUID
    accepted_at: datetime | None
    revoked_at: datetime | None
    resend_count: int
    last_sent_at: datetime
    expires_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkspaceInviteAccept(BaseModel):
    token: str
