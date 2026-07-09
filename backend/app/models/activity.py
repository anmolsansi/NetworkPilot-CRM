import logging
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.person import Person
    from app.models.user import AppUser

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)


class Activity(UUIDMixin, Base):
    __tablename__ = "activities"

    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("people.id"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id"),
        nullable=False,
        index=True,
    )
    actor_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("app_users.id"),
        nullable=False,
    )
    action_type: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    previous_stage: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_stage: Mapped[str | None] = mapped_column(Text, nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    person: Mapped["Person"] = relationship("Person", back_populates="activities")
    actor: Mapped["AppUser"] = relationship("AppUser", lazy="selectin")
