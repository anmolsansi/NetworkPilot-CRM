import logging
import uuid
from datetime import datetime, date
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.person import Person
    from app.models.user import AppUser
    from app.models.workspace import Workspace

_module_logger = logging.getLogger(__name__)

class Task(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "tasks"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("people.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("app_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="open") # open, completed
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", lazy="raise")
    person: Mapped["Person"] = relationship("Person", back_populates="tasks")
    assignee: Mapped["AppUser | None"] = relationship("AppUser", lazy="selectin")
