import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class CustomField(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "custom_fields"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    field_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # e.g. text, number, date, boolean, select
    options: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # for select type

    __table_args__ = (
        UniqueConstraint("workspace_id", "name", name="uq_custom_field_workspace_name"),
    )
