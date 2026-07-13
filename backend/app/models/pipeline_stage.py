import logging
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.person import Person
    from app.models.workspace import Workspace

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)


class PipelineStage(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "pipeline_stages"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    color: Mapped[str | None] = mapped_column(String, nullable=True)
    allowed_next_stage_ids: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )

    __table_args__ = (
        UniqueConstraint("workspace_id", "name", name="uq_pipeline_stage_workspace_name"),
        UniqueConstraint("workspace_id", "order", name="uq_pipeline_stage_workspace_order"),
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace")
    people: Mapped[list["Person"]] = relationship(
        "Person", back_populates="pipeline_stage", lazy="raise"
    )
