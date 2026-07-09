import logging
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import AppUser

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)


class UserSettings(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("app_users.id"),
        unique=True,
        nullable=False,
    )
    default_workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id"),
        nullable=True,
    )
    settings_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    user: Mapped["AppUser"] = relationship("AppUser", back_populates="user_settings")
