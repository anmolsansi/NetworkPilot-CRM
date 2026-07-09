import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.logging import get_logger, mask_id
from app.db.session import get_db
from app.models.user import AppUser
from app.models.workspace import WorkspaceMember
from app.schemas.users import UserResponse, WorkspaceMembershipResponse

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=UserResponse)
async def get_me(
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user with workspace memberships."""
    logger.info("me.get.started user_id=%s", mask_id(str(user.id)))
    result = await db.execute(
        select(WorkspaceMember)
        .where(WorkspaceMember.user_id == user.id)
        .where(WorkspaceMember.deleted_at.is_(None))
    )
    memberships = result.scalars().all()
    logger.info(
        "me.get.completed user_id=%s workspace_count=%s",
        mask_id(str(user.id)),
        len(memberships),
    )

    return UserResponse(
        id=user.id,
        supabase_user_id=user.supabase_user_id,
        email=user.email,
        display_name=user.display_name,
        created_at=user.created_at,
        updated_at=user.updated_at,
        workspaces=[
            WorkspaceMembershipResponse(
                workspace_id=m.workspace_id,
                role=m.role,
                created_at=m.created_at,
            )
            for m in memberships
        ],
    )
