import uuid
from typing import Sequence

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import AppUser
from app.schemas.workspace_invite import (
    WorkspaceInviteAccept,
    WorkspaceInviteCreate,
    WorkspaceInviteResponse,
)
from app.schemas.workspaces import WorkspaceMemberResponse
from app.services.workspace_invite_service import WorkspaceInviteService
from app.services.workspace_service import require_workspace_owner

router = APIRouter()


@router.post(
    "/workspaces/{workspace_id}/invites",
    response_model=WorkspaceInviteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invite(
    workspace_id: uuid.UUID,
    data: WorkspaceInviteCreate,
    db: AsyncSession = Depends(get_db),
    _workspace=Depends(require_workspace_owner),
) -> WorkspaceInviteResponse:
    """Create a workspace invite and send an email."""
    service = WorkspaceInviteService(db)
    return await service.create_invite(workspace_id, data)


@router.get(
    "/workspaces/{workspace_id}/invites",
    response_model=list[WorkspaceInviteResponse],
)
async def list_invites(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _workspace=Depends(require_workspace_owner),
) -> Sequence[WorkspaceInviteResponse]:
    """List pending invites for a workspace."""
    service = WorkspaceInviteService(db)
    return await service.list_invites(workspace_id)


@router.delete(
    "/workspaces/{workspace_id}/invites/{invite_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_invite(
    workspace_id: uuid.UUID,
    invite_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _workspace=Depends(require_workspace_owner),
):
    """Revoke a workspace invite."""
    service = WorkspaceInviteService(db)
    await service.revoke_invite(workspace_id, invite_id)


@router.post(
    "/invites/accept",
    response_model=WorkspaceMemberResponse,
)
async def accept_invite(
    data: WorkspaceInviteAccept,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """Accept an invite and join a workspace."""
    service = WorkspaceInviteService(db)
    return await service.accept_invite(data.token, current_user)
