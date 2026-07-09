import csv
import logging
import uuid
from datetime import date
from io import StringIO
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, ValidationError
from app.models.import_batch import ImportBatch
from app.models.person import Person
from app.schemas.activities import ActivityCreate
from app.schemas.imports import (
    IMPORT_ACTION_TYPES,
    ImportCommitRequest,
    ImportCreatedPerson,
    ImportPreviewResponse,
    ImportPreviewRow,
    ImportPreviewSummary,
)
from app.schemas.people import PersonCreate
from app.services.activity_service import ActivityService
from app.services.people_service import PeopleService
from app.services.url_normalizer import normalize_linkedin_url

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
FIELD_ALIASES = {
    "current_role": "current_role",
    "role": "current_role",
    "title": "current_role",
    "current_company": "current_company",
    "company": "current_company",
    "notes": "conversation_context",
    "conversation_context": "conversation_context",
    "linkedin": "linkedin_url",
    "linkedin_url": "linkedin_url",
    "profile_url": "linkedin_url",
}

ACTION_TO_ACTIVITY = {
    "saved_for_later": "saved_for_later",
    "invite_sent": "invite_sent",
    "already_connected": "accepted",
    "accepted_no_message": "accepted",
    "first_message_sent": "message_sent",
}


class CsvImportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def preview(
        self,
        workspace_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        content: bytes,
        file_name: str | None,
        default_initial_action_type: str = "invite_sent",
        duplicate_strategy: str = "skip",
        default_priority: str = "B",
    ) -> ImportPreviewResponse:
        if duplicate_strategy != "skip":
            raise ValidationError("Only skip duplicate strategy is supported")

        rows = self._parse_csv(content)
        preview_rows = await self._validate_rows(
            workspace_id=workspace_id,
            rows=rows,
            default_initial_action_type=default_initial_action_type,
            default_priority=default_priority,
        )
        summary = self._summarize(preview_rows)
        batch = ImportBatch(
            workspace_id=workspace_id,
            created_by_user_id=actor_user_id,
            file_name=file_name,
            total_rows=summary.total_rows,
            valid_rows=summary.valid_rows,
            duplicate_rows=summary.duplicate_rows,
            invalid_rows=summary.invalid_rows,
            created_count=0,
            status="previewed",
        )
        self.db.add(batch)
        await self.db.flush()
        return ImportPreviewResponse(summary=summary, rows=preview_rows, import_batch_id=batch.id)

    async def commit(
        self,
        actor_user_id: uuid.UUID,
        data: ImportCommitRequest,
    ) -> dict[str, Any]:
        if data.duplicate_strategy != "skip":
            raise ValidationError("Only skip duplicate strategy is supported")

        raw_rows = [row.model_dump() for row in data.rows]
        preview_rows = await self._validate_rows(
            workspace_id=data.workspace_id,
            rows=raw_rows,
            default_initial_action_type=data.default_initial_action_type,
            default_priority=data.default_priority,
        )

        people_service = PeopleService(self.db)
        activity_service = ActivityService(self.db)
        created_people: list[ImportCreatedPerson] = []
        errors: list[ImportPreviewRow] = []

        for row in preview_rows:
            if row.status != "valid":
                errors.append(row)
                continue

            try:
                person = await people_service.create(
                    data.workspace_id,
                    PersonCreate(
                        name=row.name or "",
                        linkedin_url=row.linkedin_url or "",
                        role=row.current_role,
                        company=row.current_company,
                        location=row.location,
                        priority=row.priority or data.default_priority,
                        connection_note=row.connection_note,
                        notes=row.conversation_context,
                        tags=row.tags or None,
                    ),
                )
                action_type = ACTION_TO_ACTIVITY[
                    row.initial_action_type or data.default_initial_action_type
                ]
                _activity, person = await activity_service.create(
                    data.workspace_id,
                    person.id,
                    actor_user_id,
                    ActivityCreate(
                        action_type=action_type,
                        source="csv_import",
                        notes="Created from CSV import",
                        next_action_date=row.next_action_date,
                    ),
                )
                created_people.append(
                    ImportCreatedPerson(
                        id=person.id,
                        name=person.name,
                        normalized_profile_url=person.linkedin_url,
                        stage=person.stage,
                        next_action_type=person.next_action_type,
                        next_action_date=person.next_action_date,
                    )
                )
            except (ConflictError, ValidationError) as exc:
                row.status = "invalid"
                row.errors.append(str(exc))
                errors.append(row)

        if data.import_batch_id:
            batch = await self.db.get(ImportBatch, data.import_batch_id)
            if batch and batch.workspace_id == data.workspace_id:
                batch.created_count = len(created_people)
                batch.status = "committed"

        return {
            "summary": {
                "created_count": len(created_people),
                "skipped_duplicates": sum(1 for row in preview_rows if row.status == "duplicate"),
                "failed_count": len(errors),
            },
            "created_people": created_people,
            "errors": errors,
        }

    def _parse_csv(self, content: bytes) -> list[dict[str, Any]]:
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValidationError("CSV must be UTF-8 encoded") from exc

        reader = csv.DictReader(StringIO(text))
        if not reader.fieldnames:
            raise ValidationError("CSV must include a header row")

        normalized_fields = [self._normalize_header(field) for field in reader.fieldnames]
        rows: list[dict[str, Any]] = []
        for raw_row in reader:
            mapped: dict[str, Any] = {}
            for original, normalized in zip(reader.fieldnames, normalized_fields, strict=False):
                field = FIELD_ALIASES.get(normalized, normalized)
                mapped[field] = (raw_row.get(original) or "").strip()
            rows.append(mapped)
        return rows

    async def _validate_rows(
        self,
        workspace_id: uuid.UUID,
        rows: list[dict[str, Any]],
        default_initial_action_type: str,
        default_priority: str,
    ) -> list[ImportPreviewRow]:
        self._validate_defaults(default_initial_action_type, default_priority)
        normalized_urls = [
            normalize_linkedin_url((row.get("linkedin_url") or "").strip())
            for row in rows
        ]
        existing_urls = await self._existing_urls(
            workspace_id,
            [result[0] for result in normalized_urls if result],
        )
        seen_urls: set[str] = set()
        preview_rows: list[ImportPreviewRow] = []

        for index, row in enumerate(rows, start=2):
            errors: list[str] = []
            name = self._clean(row.get("name"))
            linkedin_url = self._clean(row.get("linkedin_url"))
            normalized = normalize_linkedin_url(linkedin_url or "")
            normalized_url = normalized[0] if normalized else None

            if not name:
                errors.append("name is required")
            if not linkedin_url:
                errors.append("linkedin_url is required")
            elif not normalized:
                errors.append("linkedin_url must be a LinkedIn profile URL")

            priority = (self._clean(row.get("priority")) or default_priority).upper()
            if priority not in {"A", "B", "C"}:
                errors.append("priority must be A, B, or C")

            initial_action_type = (
                self._clean(row.get("initial_action_type")) or default_initial_action_type
            )
            if initial_action_type == "custom_from_csv":
                errors.append(
                    "initial_action_type must be provided per row when using custom_from_csv"
                )
            elif initial_action_type not in IMPORT_ACTION_TYPES:
                errors.append("initial_action_type is invalid")

            next_action_date = self._parse_date(row.get("next_action_date"), errors)

            status = "invalid" if errors else "valid"
            if not errors and normalized_url:
                if normalized_url in existing_urls or normalized_url in seen_urls:
                    status = "duplicate"
                else:
                    seen_urls.add(normalized_url)

            preview_rows.append(
                ImportPreviewRow(
                    row_number=index,
                    status=status,
                    name=name,
                    linkedin_url=linkedin_url,
                    normalized_profile_url=normalized_url,
                    errors=errors,
                    current_role=self._clean(row.get("current_role")),
                    current_company=self._clean(row.get("current_company")),
                    location=self._clean(row.get("location")),
                    priority=priority,
                    connection_note=self._clean(row.get("connection_note")),
                    conversation_context=self._clean(row.get("conversation_context")),
                    tags=self._parse_tags(row.get("tags")),
                    initial_action_type=initial_action_type,
                    next_action_date=next_action_date,
                )
            )
        return preview_rows

    async def _existing_urls(self, workspace_id: uuid.UUID, urls: list[str]) -> set[str]:
        if not urls:
            return set()
        result = await self.db.execute(
            select(Person.linkedin_url).where(
                Person.workspace_id == workspace_id,
                Person.linkedin_url.in_(urls),
                Person.deleted_at.is_(None),
            )
        )
        return set(result.scalars().all())

    def _validate_defaults(self, default_initial_action_type: str, default_priority: str) -> None:
        if (
            default_initial_action_type not in IMPORT_ACTION_TYPES
            and default_initial_action_type != "custom_from_csv"
        ):
            raise ValidationError("default_initial_action_type is invalid")
        if default_priority not in {"A", "B", "C"}:
            raise ValidationError("default_priority must be A, B, or C")

    def _summarize(self, rows: list[ImportPreviewRow]) -> ImportPreviewSummary:
        return ImportPreviewSummary(
            total_rows=len(rows),
            valid_rows=sum(1 for row in rows if row.status == "valid"),
            duplicate_rows=sum(1 for row in rows if row.status == "duplicate"),
            invalid_rows=sum(1 for row in rows if row.status == "invalid"),
        )

    def _normalize_header(self, header: str) -> str:
        return header.strip().lower().replace(" ", "_").replace("-", "_")

    def _clean(self, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, list):
            return None
        text = str(value).strip()
        return text or None

    def _parse_tags(self, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        delimiter = ";" if ";" in str(value) else ","
        return [tag.strip() for tag in str(value).split(delimiter) if tag.strip()]

    def _parse_date(self, value: Any, errors: list[str]) -> date | None:
        text = self._clean(value)
        if not text:
            return None
        try:
            return date.fromisoformat(text)
        except ValueError:
            errors.append("next_action_date must be YYYY-MM-DD")
            return None
