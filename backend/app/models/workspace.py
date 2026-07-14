import logging
import uuid
from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, Text, Time
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.person import Person
    from app.models.template import MessageTemplate
    from app.models.user import AppUser

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)


class Workspace(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "workspaces"

    name: Mapped[str] = mapped_column(Text, nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("app_users.id"),
        nullable=False,
        index=True,
    )
    default_follow_up_delay_days: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    default_acceptance_check_delay_days: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False
    )
    daily_reminder_time: Mapped[time] = mapped_column(Time, default=time(9, 0), nullable=False)
    timezone: Mapped[str] = mapped_column(Text, default="UTC", nullable=False)
    quiet_hours_start: Mapped[time | None] = mapped_column(Time, nullable=True)
    quiet_hours_end: Mapped[time | None] = mapped_column(Time, nullable=True)
    email_reminders_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    daily_digest_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    overdue_alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    owner: Mapped["AppUser"] = relationship("AppUser", lazy="selectin")
    members: Mapped[list["WorkspaceMember"]] = relationship(
        "WorkspaceMember", back_populates="workspace", lazy="selectin"
    )
    people: Mapped[list["Person"]] = relationship(
        "Person", back_populates="workspace", lazy="selectin"
    )
    templates: Mapped[list["MessageTemplate"]] = relationship(
        "MessageTemplate", back_populates="workspace", lazy="selectin"
    )


class WorkspaceMember(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "workspace_members"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("app_users.id"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(Text, nullable=False, default="member")
    dashboard_config: Mapped[dict] = mapped_column(
        postgresql.JSONB(astext_type=Text()), server_default="{}", nullable=False
    )
    weekly_outreach_target: Mapped[int] = mapped_column(
        Integer, server_default="50", nullable=False
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="members")
    user: Mapped["AppUser"] = relationship("AppUser", back_populates="workspace_memberships")
