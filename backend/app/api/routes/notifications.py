import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.notification import Notification
from app.models.user import AppUser
from app.schemas.notifications import NotificationResponse
from app.services.workspace_service import require_workspace_access

router = APIRouter()


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    workspace_id: uuid.UUID = Query(...),
    unread_only: bool = Query(False),
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_workspace_access(workspace_id, user, db)
    stmt = select(Notification).where(
        Notification.workspace_id == workspace_id,
        Notification.user_id == user.id,
    )
    if unread_only:
        stmt = stmt.where(Notification.is_read.is_(False))
    result = await db.execute(stmt.order_by(Notification.created_at.desc()).limit(100))
    return list(result.scalars().all())


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: uuid.UUID,
    workspace_id: uuid.UUID = Query(...),
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_workspace_access(workspace_id, user, db)
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.workspace_id == workspace_id,
            Notification.user_id == user.id,
        )
    )
    notification = result.scalar_one_or_none()
    if notification is None:
        from app.core.errors import NotFoundError

        raise NotFoundError("Notification", str(notification_id))
    notification.is_read = True
    await db.flush()
    return notification


@router.post("/read-all", status_code=204)
async def mark_all_notifications_read(
    workspace_id: uuid.UUID = Query(...),
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_workspace_access(workspace_id, user, db)
    await db.execute(
        update(Notification)
        .where(Notification.workspace_id == workspace_id, Notification.user_id == user.id)
        .values(is_read=True)
    )
