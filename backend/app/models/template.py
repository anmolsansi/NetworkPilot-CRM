import logging
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ARRAY, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.workspace import Workspace

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)


class MessageTemplate(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "message_templates"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="templates")
