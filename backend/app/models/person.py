import logging
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.activity import Activity
    from app.models.pipeline_stage import PipelineStage
    from app.models.tag import Tag
    from app.models.task import Task
    from app.models.user import AppUser
    from app.models.workspace import Workspace

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)


class Person(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "people"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    first_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    linkedin_url: Mapped[str] = mapped_column(Text, nullable=False)
    linkedin_slug: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    role: Mapped[str | None] = mapped_column(Text, nullable=True)
    company: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone_number: Mapped[str | None] = mapped_column(Text, nullable=True)
    premium: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    company_website: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_at_millis: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    invite_accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    invite_accepted_at_millis: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_favorite: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    favorite_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(1), nullable=False, default="B")
    stage: Mapped[str] = mapped_column(Text, nullable=False, default="invite_sent")
    status: Mapped[str] = mapped_column(Text, nullable=False, default="active")
    next_action_type: Mapped[str | None] = mapped_column(String, nullable=True)
    next_action_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    tags: Mapped[list["Tag"]] = relationship("Tag", secondary="person_tags", lazy="selectin")
    last_action_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_action_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    connection_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    custom_fields_data: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, server_default="{}"
    )
    manual_warmth: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    calculated_freshness: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_engaged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    stage_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pipeline_stages.id", ondelete="SET NULL"),
        nullable=True,
    )

    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("app_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="people")
    pipeline_stage: Mapped["PipelineStage"] = relationship("PipelineStage", back_populates="people")
    activities: Mapped[list["Activity"]] = relationship(
        "Activity", back_populates="person", lazy="raise"
    )
    owner: Mapped["AppUser | None"] = relationship("AppUser", lazy="selectin")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="person", lazy="raise")
