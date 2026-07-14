import logging
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Sequence

import resend
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.models.user import AppUser
from app.models.workspace import Workspace, WorkspaceMember
from app.models.workspace_invite import WorkspaceInvite
from app.schemas.workspace_invite import WorkspaceInviteCreate

logger = logging.getLogger(__name__)


class WorkspaceInviteService:
    def __init__(self, db: AsyncSession):
        self.db = db
        if settings.RESEND_API_KEY:
            resend.api_key = settings.RESEND_API_KEY

    async def list_invites(self, workspace_id: uuid.UUID) -> Sequence[WorkspaceInvite]:
        result = await self.db.execute(
            select(WorkspaceInvite).where(WorkspaceInvite.workspace_id == workspace_id)
        )
        return result.scalars().all()

    async def create_invite(
        self, workspace_id: uuid.UUID, data: WorkspaceInviteCreate
    ) -> WorkspaceInvite:
        # Check if already a member
        existing_member = await self.db.execute(
            select(WorkspaceMember)
            .join(AppUser, AppUser.id == WorkspaceMember.user_id)
            .where(
                WorkspaceMember.workspace_id == workspace_id,
                AppUser.email == data.email,
            )
        )
        if existing_member.scalar_one_or_none():
            raise ConflictError("User is already a member of this workspace")

        # Check if invite already exists
        existing_invite = await self.db.execute(
            select(WorkspaceInvite).where(
                WorkspaceInvite.workspace_id == workspace_id,
                WorkspaceInvite.email == data.email,
            )
        )
        invite = existing_invite.scalar_one_or_none()

        if invite:
            # Refresh token and expiry
            invite.token = secrets.token_urlsafe(32)
            invite.expires_at = datetime.utcnow() + timedelta(days=7)
        else:
            invite = WorkspaceInvite(
                workspace_id=workspace_id,
                email=data.email,
                role=data.role,
                token=secrets.token_urlsafe(32),
                expires_at=datetime.utcnow() + timedelta(days=7),
            )
            self.db.add(invite)

        await self.db.flush()

        # Get workspace name for the email
        ws = (
            await self.db.execute(select(Workspace).where(Workspace.id == workspace_id))
        ).scalar_one()

        if settings.RESEND_API_KEY and settings.RESEND_FROM_EMAIL:
            invite_url = f"{settings.FRONTEND_URL}/invites/accept?token={invite.token}"
            try:
                resend.Emails.send(
                    {
                        "from": settings.RESEND_FROM_EMAIL,
                        "to": data.email,
                        "subject": f"You have been invited to join {ws.name}",
                        "html": f"<p>You've been invited to join the <strong>{ws.name}</strong> workspace.</p><p><a href='{invite_url}'>Click here to accept the invitation</a>.</p>",
                    }
                )
            except Exception as e:
                logger.error(f"Failed to send invite email to {data.email}: {e}")
                # We do not fail the request, but log the error

        return invite

    async def revoke_invite(self, workspace_id: uuid.UUID, invite_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(WorkspaceInvite).where(
                WorkspaceInvite.id == invite_id,
                WorkspaceInvite.workspace_id == workspace_id,
            )
        )
        invite = result.scalar_one_or_none()
        if not invite:
            raise NotFoundError("WorkspaceInvite", str(invite_id))

        await self.db.delete(invite)
        await self.db.flush()

    async def accept_invite(self, token: str, user: AppUser) -> WorkspaceMember:
        result = await self.db.execute(
            select(WorkspaceInvite).where(WorkspaceInvite.token == token)
        )
        invite = result.scalar_one_or_none()

        if not invite:
            raise ValidationError("Invalid or expired invitation token.")

        if invite.expires_at < datetime.utcnow():
            raise ValidationError("Invitation has expired.")

        if user.email.lower() != invite.email.lower():
            raise ValidationError("This invitation is not for your email address.")

        # Check if already a member
        existing_member = await self.db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == invite.workspace_id,
                WorkspaceMember.user_id == user.id,
            )
        )
        member = existing_member.scalar_one_or_none()

        if member:
            # Already a member, just delete the invite and return
            await self.db.delete(invite)
            await self.db.flush()
            return member

        # Create member
        member = WorkspaceMember(
            workspace_id=invite.workspace_id,
            user_id=user.id,
            role=invite.role,
        )
        self.db.add(member)
        await self.db.delete(invite)
        await self.db.flush()

        return member
