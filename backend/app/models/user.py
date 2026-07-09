import logging
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.settings import UserSettings
    from app.models.workspace import WorkspaceMember

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)


class AppUser(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "app_users"

    supabase_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    workspace_memberships: Mapped[list["WorkspaceMember"]] = relationship(
        "WorkspaceMember", back_populates="user", lazy="selectin"
    )
    user_settings: Mapped["UserSettings | None"] = relationship(
        "UserSettings", back_populates="user", uselist=False, lazy="selectin"
    )
