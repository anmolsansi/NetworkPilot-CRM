import logging
import uuid

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.errors import ForbiddenError, NotFoundError
from app.core.logging import mask_id
from app.db.session import get_db
from app.models.user import AppUser
from app.models.workspace import Workspace, WorkspaceMember

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)


async def get_workspace_or_404(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    """Get workspace or raise 404."""
    _module_logger.debug(
        "workspace_service.get.started workspace_id=%s",
        mask_id(str(workspace_id)),
    )
    result = await db.execute(
        select(Workspace).where(
            Workspace.id == workspace_id,
            Workspace.deleted_at.is_(None),
        )
    )
    workspace = result.scalar_one_or_none()

    if not workspace:
        _module_logger.warning(
            "workspace_service.get.missing workspace_id=%s",
            mask_id(str(workspace_id)),
        )
        raise NotFoundError("Workspace", str(workspace_id))

    _module_logger.debug(
        "workspace_service.get.completed workspace_id=%s",
        mask_id(str(workspace.id)),
    )
    return workspace


async def require_workspace_access(
    workspace_id: uuid.UUID,
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    """Require user to be a member of the workspace."""
    _module_logger.debug(
        "workspace_service.access.started workspace_id=%s user_id=%s",
        mask_id(str(workspace_id)),
        mask_id(str(user.id)),
    )
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user.id,
            WorkspaceMember.deleted_at.is_(None),
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        _module_logger.warning(
            "workspace_service.access.denied workspace_id=%s user_id=%s",
            mask_id(str(workspace_id)),
            mask_id(str(user.id)),
        )
        raise ForbiddenError("You do not have access to this workspace")

    # Also verify workspace exists
    workspace = await get_workspace_or_404(workspace_id, db)
    _module_logger.debug(
        "workspace_service.access.allowed workspace_id=%s user_id=%s role=%s",
        mask_id(str(workspace_id)),
        mask_id(str(user.id)),
        membership.role,
    )
    return workspace


async def require_workspace_owner(
    workspace_id: uuid.UUID,
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    """Require user to be the owner of the workspace."""
    _module_logger.debug(
        "workspace_service.owner_check.started workspace_id=%s user_id=%s",
        mask_id(str(workspace_id)),
        mask_id(str(user.id)),
    )
    workspace = await get_workspace_or_404(workspace_id, db)

    if workspace.owner_id != user.id:
        _module_logger.warning(
            "workspace_service.owner_check.denied workspace_id=%s user_id=%s owner_id=%s",
            mask_id(str(workspace_id)),
            mask_id(str(user.id)),
            mask_id(str(workspace.owner_id)),
        )
        raise ForbiddenError("Only workspace owner can perform this action")

    _module_logger.debug(
        "workspace_service.owner_check.allowed workspace_id=%s user_id=%s",
        mask_id(str(workspace_id)),
        mask_id(str(user.id)),
    )
    return workspace
