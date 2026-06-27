import uuid
from datetime import date, datetime

from sqlalchemy import ARRAY, DateTime, Date, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin


class Person(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "people"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    linkedin_url: Mapped[str] = mapped_column(Text, nullable=False)
    linkedin_slug: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    role: Mapped[str | None] = mapped_column(Text, nullable=True)
    company: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(1), nullable=False, default="B")
    stage: Mapped[str] = mapped_column(Text, nullable=False, default="invite_sent")
    status: Mapped[str] = mapped_column(Text, nullable=False, default="active")
    next_action_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_action_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_action_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_action_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    connection_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="people")
    activities: Mapped[list["Activity"]] = relationship(
        "Activity", back_populates="person", lazy="selectin"
    )
