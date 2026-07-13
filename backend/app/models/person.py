import logging
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import ARRAY, BigInteger, Boolean, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.activity import Activity
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
    invite_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    invite_accepted_at_millis: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
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
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="people")
    activities: Mapped[list["Activity"]] = relationship(
        "Activity", back_populates="person", lazy="raise"
    )
