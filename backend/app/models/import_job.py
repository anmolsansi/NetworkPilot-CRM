import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, Integer, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class ImportJob(Base):
    __tablename__ = "import_jobs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("app_users.id", ondelete="RESTRICT"), nullable=False)
    
    status: Mapped[str] = mapped_column(String, default="pending", nullable=False)
    file_content: Mapped[str] = mapped_column(Text, nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_log: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
