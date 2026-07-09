import logging
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
if TYPE_CHECKING:
    from app.models.user import AppUser
    from app.models.workspace import Workspace


class ImportBatch(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "import_batches"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id"),
        nullable=False,
        index=True,
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("app_users.id"),
        nullable=False,
        index=True,
    )
    file_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valid_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicate_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    invalid_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="previewed")

    workspace: Mapped["Workspace"] = relationship("Workspace", lazy="selectin")
    created_by: Mapped["AppUser"] = relationship("AppUser", lazy="selectin")
