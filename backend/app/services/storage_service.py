import asyncio
import logging
import uuid
from dataclasses import dataclass
from pathlib import Path

import boto3
from botocore.config import Config
from fastapi import HTTPException, UploadFile

from app.core.config import settings
from app.core.logging import mask_id

_module_logger = logging.getLogger(__name__)

MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
DOWNLOAD_URL_TTL_SECONDS = 300
ALLOWED_EXTENSIONS_BY_TYPE = {
    "application/pdf": {".pdf"},
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"},
    "image/webp": {".webp"},
    "text/csv": {".csv"},
    "text/plain": {".txt"},
}


@dataclass(frozen=True)
class StoredFile:
    object_key: str
    file_size: int
    content_type: str


class StorageService:
    def __init__(self, client=None, bucket_name: str | None = None):
        self.bucket_name = bucket_name or settings.R2_BUCKET_NAME
        if client is not None:
            self.client = client
            return

        required = {
            "R2_ACCOUNT_ID": settings.R2_ACCOUNT_ID,
            "R2_ACCESS_KEY_ID": settings.R2_ACCESS_KEY_ID,
            "R2_SECRET_ACCESS_KEY": settings.R2_SECRET_ACCESS_KEY,
            "R2_BUCKET_NAME": self.bucket_name,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise RuntimeError(f"Cloudflare R2 is not configured: {', '.join(missing)}")

        self.client = boto3.client(
            "s3",
            endpoint_url=(
                f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
            ),
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name="auto",
            config=Config(
                connect_timeout=5,
                read_timeout=30,
                retries={"max_attempts": 3, "mode": "standard"},
            ),
        )

    async def save_file(
        self,
        workspace_id: uuid.UUID,
        activity_id: uuid.UUID,
        file: UploadFile,
    ) -> StoredFile:
        """Validate and store an attachment in the private R2 bucket."""
        content_type = file.content_type or "application/octet-stream"
        extension = Path(file.filename or "").suffix.lower()
        allowed_extensions = ALLOWED_EXTENSIONS_BY_TYPE.get(content_type)
        if not allowed_extensions or extension not in allowed_extensions:
            raise HTTPException(
                status_code=422,
                detail="Unsupported attachment type or file extension",
            )

        content = await file.read(MAX_ATTACHMENT_BYTES + 1)
        if len(content) > MAX_ATTACHMENT_BYTES:
            raise HTTPException(status_code=413, detail="Attachments must be 10 MB or smaller")
        if not content:
            raise HTTPException(status_code=422, detail="Attachments cannot be empty")
        self._validate_signature(content_type, content)

        object_key = (
            f"workspaces/{workspace_id}/activities/{activity_id}/"
            f"{uuid.uuid4()}{extension}"
        )
        try:
            await asyncio.to_thread(
                self.client.put_object,
                Bucket=self.bucket_name,
                Key=object_key,
                Body=content,
                ContentType=content_type,
            )
        except Exception as exc:
            _module_logger.exception(
                "storage_service.upload.failed workspace_id=%s activity_id=%s",
                mask_id(str(workspace_id)),
                mask_id(str(activity_id)),
            )
            raise HTTPException(
                status_code=503,
                detail="Attachment storage is unavailable",
            ) from exc

        _module_logger.info(
            "storage_service.upload.completed workspace_id=%s activity_id=%s size=%s",
            mask_id(str(workspace_id)),
            mask_id(str(activity_id)),
            len(content),
        )
        return StoredFile(object_key, len(content), content_type)

    def create_download_url(self, object_key: str) -> str:
        """Create a short-lived URL for one private object."""
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": object_key},
            ExpiresIn=DOWNLOAD_URL_TTL_SECONDS,
        )

    async def delete_file(self, object_key: str) -> None:
        """Delete an object from the private R2 bucket."""
        try:
            await asyncio.to_thread(
                self.client.delete_object,
                Bucket=self.bucket_name,
                Key=object_key,
            )
        except Exception as exc:
            _module_logger.exception("storage_service.delete.failed")
            raise HTTPException(
                status_code=503,
                detail="Attachment storage is unavailable",
            ) from exc

    @staticmethod
    def _validate_signature(content_type: str, content: bytes) -> None:
        valid = True
        if content_type == "application/pdf":
            valid = content.startswith(b"%PDF-")
        elif content_type == "image/png":
            valid = content.startswith(b"\x89PNG\r\n\x1a\n")
        elif content_type == "image/jpeg":
            valid = content.startswith(b"\xff\xd8\xff")
        elif content_type == "image/webp":
            valid = len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP"
        elif content_type.startswith("text/"):
            try:
                content.decode("utf-8")
                valid = b"\x00" not in content
            except UnicodeDecodeError:
                valid = False
        if not valid:
            raise HTTPException(
                status_code=422,
                detail="Attachment contents do not match the declared file type",
            )
