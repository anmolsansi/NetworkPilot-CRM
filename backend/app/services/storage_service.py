import logging
import os
import shutil
import uuid
from pathlib import Path
from fastapi import UploadFile

from app.core.config import settings

_module_logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        # We use a simple local directory for V1.
        self.upload_dir = Path(settings.UPLOAD_DIR) if hasattr(settings, "UPLOAD_DIR") else Path("/tmp/networkpilot_uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(self, workspace_id: uuid.UUID, file: UploadFile) -> str:
        """Save an uploaded file and return its storage path."""
        workspace_dir = self.upload_dir / str(workspace_id)
        workspace_dir.mkdir(parents=True, exist_ok=True)

        file_id = str(uuid.uuid4())
        ext = os.path.splitext(file.filename)[1] if file.filename else ""
        storage_filename = f"{file_id}{ext}"
        storage_path = workspace_dir / storage_filename

        with storage_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        _module_logger.info("storage_service.save_file.completed workspace_id=%s path=%s", workspace_id, storage_path)
        return str(storage_path)

    def delete_file(self, storage_path: str) -> None:
        """Delete a file from storage."""
        path = Path(storage_path)
        if path.exists():
            path.unlink()
            _module_logger.info("storage_service.delete_file.completed path=%s", storage_path)
