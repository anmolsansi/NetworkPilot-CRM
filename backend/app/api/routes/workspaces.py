import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.errors import ForbiddenError, NotFoundError
from app.models.user import AppUser
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.workspaces import (
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceUpdate,
)
from app.services.workspace_service import require_workspace_owner

router = APIRouter()


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List workspaces the user is a member of."""
    result = await db.execute(
        select(Workspace)
        .join(WorkspaceMember)
        .where(
            WorkspaceMember.user_id == user.id,
            WorkspaceMember.deleted_at.is_(None),
            Workspace.deleted_at.is_(None),
        )
    )
    return result.scalars().all()


@router.post("", response_model=WorkspaceResponse, status_code=201)
async def create_workspace(
    data: WorkspaceCreate,
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new workspace and add user as owner."""
    workspace = Workspace(
        name=data.name,
        owner_id=user.id,
        default_follow_up_delay_days=data.default_follow_up_delay_days,
        default_acceptance_check_delay_days=data.default_acceptance_check_delay_days,
        timezone=data.timezone,
    )
    db.add(workspace)
    await db.flush()

    # Add owner membership
    membership = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=user.id,
        role="owner",
    )
    db.add(membership)
    await db.flush()

    return workspace


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: uuid.UUID,
    data: WorkspaceUpdate,
    workspace: Workspace = Depends(require_workspace_owner),
    db: AsyncSession = Depends(get_db),
):
    """Update workspace settings (owner only)."""
    update_data = data.model_dump(exclude_unset=True)

    # Handle daily_reminder_time string -> time conversion
    if "daily_reminder_time" in update_data and update_data["daily_reminder_time"] is not None:
        time_str = update_data["daily_reminder_time"]
        h, m = map(int, time_str.split(":"))
        from datetime import time
        update_data["daily_reminder_time"] = time(h, m)

    for field, value in update_data.items():
        setattr(workspace, field, value)

    await db.flush()
    return workspace
