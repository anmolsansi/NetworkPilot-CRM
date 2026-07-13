import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class PersonMerge(Base):
    __tablename__ = "person_merges"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False)
    target_person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"), index=True, nullable=False)
    source_person_id: Mapped[uuid.UUID] = mapped_column(index=True, nullable=False)
    merged_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_users.id", ondelete="RESTRICT"), nullable=False)
    merge_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
