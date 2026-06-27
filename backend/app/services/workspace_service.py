import uuid

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.errors import ForbiddenError, NotFoundError
from app.db.session import get_db as get_db_session
from app.models.user import AppUser
from app.models.workspace import Workspace, WorkspaceMember


async def get_workspace_or_404(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    """Get workspace or raise 404."""
    result = await db.execute(
        select(Workspace).where(
            Workspace.id == workspace_id,
            Workspace.deleted_at.is_(None),
        )
    )
    workspace = result.scalar_one_or_none()

    if not workspace:
        raise NotFoundError("Workspace", str(workspace_id))

    return workspace


async def require_workspace_access(
    workspace_id: uuid.UUID,
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    """Require user to be a member of the workspace."""
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user.id,
            WorkspaceMember.deleted_at.is_(None),
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise ForbiddenError("You do not have access to this workspace")

    # Also verify workspace exists
    return await get_workspace_or_404(workspace_id, db)


async def require_workspace_owner(
    workspace_id: uuid.UUID,
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    """Require user to be the owner of the workspace."""
    workspace = await get_workspace_or_404(workspace_id, db)

    if workspace.owner_id != user.id:
        raise ForbiddenError("Only workspace owner can perform this action")

    return workspace
