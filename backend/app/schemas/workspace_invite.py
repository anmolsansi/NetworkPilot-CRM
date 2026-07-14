from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict, EmailStr

class WorkspaceInviteCreate(BaseModel):
    email: EmailStr
    role: str = "member"

class WorkspaceInviteResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    email: str
    role: str
    expires_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class WorkspaceInviteAccept(BaseModel):
    token: str
