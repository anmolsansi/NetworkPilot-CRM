import logging
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.logging import get_logger, mask_id
from app.models.user import AppUser
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.workspaces import (
    WorkspaceCreate,
    WorkspaceMemberDirectoryEntry,
    WorkspaceMemberResponse,
    WorkspaceMemberUpdate,
    WorkspaceResponse,
    WorkspaceUpdate,
)
from app.services.workspace_service import require_workspace_access, require_workspace_owner

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
router = APIRouter()
logger = get_logger(__name__)


@router.get(
    "/{workspace_id}/members",
    response_model=list[WorkspaceMemberDirectoryEntry],
)
async def list_workspace_members(
    workspace_id: uuid.UUID,
    _workspace=Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """List active members available for ownership and assignment."""
    result = await db.execute(
        select(WorkspaceMember, AppUser)
        .join(AppUser, AppUser.id == WorkspaceMember.user_id)
        .where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.deleted_at.is_(None),
            AppUser.deleted_at.is_(None),
        )
        .order_by(AppUser.display_name.asc().nullslast(), AppUser.email.asc())
    )
    return [
        WorkspaceMemberDirectoryEntry(
            user_id=member.user_id,
            email=user.email,
            display_name=user.display_name,
            role=member.role,
        )
        for member, user in result.all()
    ]


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List workspaces the user is a member of."""
    logger.info("workspaces.list.started user_id=%s", mask_id(str(user.id)))
    result = await db.execute(
        select(Workspace)
        .join(WorkspaceMember)
        .where(
            WorkspaceMember.user_id == user.id,
            WorkspaceMember.deleted_at.is_(None),
            Workspace.deleted_at.is_(None),
        )
    )
    workspaces = result.scalars().all()
    logger.info(
        "workspaces.list.completed user_id=%s count=%s",
        mask_id(str(user.id)),
        len(workspaces),
    )
    return workspaces


@router.post("", response_model=WorkspaceResponse, status_code=201)
async def create_workspace(
    data: WorkspaceCreate,
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new workspace and add user as owner."""
    logger.info(
        "workspaces.create.started user_id=%s name_length=%s timezone=%s",
        mask_id(str(user.id)),
        len(data.name),
        data.timezone,
    )
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

    # Schedule the initial daily digest for this workspace
    from datetime import datetime, timedelta

    from app.models.background_job import BackgroundJob

    # Calculate next run time
    now = datetime.utcnow()
    next_run_date = now.date() + timedelta(days=1)

    # If the workspace has a specific daily_reminder_time (it defaults to 9:00), use it
    next_run = datetime.combine(next_run_date, workspace.daily_reminder_time)

    job = BackgroundJob(
        workspace_id=workspace.id, job_type="daily_digest", status="pending", run_at=next_run
    )
    db.add(job)
    db.add(
        BackgroundJob(
            workspace_id=workspace.id,
            job_type="relationship_health_refresh",
            status="pending",
            run_at=next_run,
        )
    )
    await db.flush()

    logger.info(
        "workspaces.create.completed user_id=%s workspace_id=%s",
        mask_id(str(user.id)),
        mask_id(str(workspace.id)),
    )
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
    logger.info(
        "workspaces.update.started workspace_id=%s fields=%s",
        mask_id(str(workspace_id)),
        sorted(update_data.keys()),
    )

    for time_field in ("daily_reminder_time", "quiet_hours_start", "quiet_hours_end"):
        if time_field in update_data and update_data[time_field] is not None:
            h, m = map(int, update_data[time_field].split(":"))
            from datetime import time

            update_data[time_field] = time(h, m)

    for field, value in update_data.items():
        setattr(workspace, field, value)

    await db.flush()
    logger.info("workspaces.update.completed workspace_id=%s", mask_id(str(workspace.id)))
    return workspace


@router.post("/{workspace_id}/trigger_digest")
async def trigger_digest(
    workspace_id: uuid.UUID,
    workspace: Workspace = Depends(require_workspace_owner),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger a digest email job for testing."""
    from datetime import datetime

    from app.models.background_job import BackgroundJob

    job = BackgroundJob(
        workspace_id=workspace_id,
        job_type="daily_digest",
        status="pending",
        run_at=datetime.utcnow(),
    )
    db.add(job)
    await db.flush()
    return {"status": "queued", "job_id": str(job.id)}


@router.get(
    "/{workspace_id}/members/me",
    response_model=WorkspaceMemberResponse,
)
async def get_member_settings(
    workspace_id: uuid.UUID,
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get workspace member settings like dashboard config."""
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user.id,
        )
    )
    from app.core.errors import NotFoundError

    member = result.scalar_one_or_none()
    if not member:
        raise NotFoundError("WorkspaceMember", str(user.id))
    return member


@router.patch(
    "/{workspace_id}/members/me",
    response_model=WorkspaceMemberResponse,
)
async def update_member_settings(
    workspace_id: uuid.UUID,
    data: WorkspaceMemberUpdate,
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update workspace member settings like dashboard config."""
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user.id,
        )
    )
    from app.core.errors import NotFoundError

    member = result.scalar_one_or_none()
    if not member:
        raise NotFoundError("WorkspaceMember", str(user.id))

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(member, field, value)

    await db.flush()
    await db.refresh(member)
    return member
