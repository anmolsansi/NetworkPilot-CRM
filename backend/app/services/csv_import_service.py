import csv
import logging
import uuid
from datetime import date, datetime, timezone
from io import StringIO
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, ValidationError
from app.models.import_batch import ImportBatch
from app.models.person import Person
from app.models.tag import Tag
from app.models.workspace import Workspace
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
    "link": "linkedin_url",
    "position": "current_role",
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
        workspace = await self.db.get(Workspace, data.workspace_id)
        created_people: list[ImportCreatedPerson] = []
        errors: list[ImportPreviewRow] = []

        for row in preview_rows:
            if row.status != "valid":
                errors.append(row)
                continue

            try:
                tag_ids = await self._resolve_tag_names(data.workspace_id, row.tags)
                person = await people_service.create(
                    data.workspace_id,
                    PersonCreate(
                        name=row.name or "",
                        first_name=row.first_name,
                        last_name=row.last_name,
                        linkedin_url=row.linkedin_url or "",
                        role=row.current_role,
                        company=row.current_company,
                        location=row.location,
                        email=row.email,
                        phone_number=row.phone_number,
                        premium=row.premium,
                        company_website=row.company_website,
                        processed_at=row.processed_at,
                        processed_at_millis=row.processed_at_millis,
                        invite_accepted_at=row.invite_accepted_at,
                        invite_accepted_at_millis=row.invite_accepted_at_millis,
                        priority=row.priority or data.default_priority,
                        connection_note=row.connection_note,
                        notes=row.conversation_context,
                        tag_ids=tag_ids,
                    ),
                    check_duplicate=False,
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
                    person=person,
                    workspace=workspace,
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
                batch.created_count += len(created_people)
                batch.status = (
                    "committed" if data.chunk_index + 1 >= data.total_chunks else "importing"
                )

        return {
            "summary": {
                "created_count": len(created_people),
                "skipped_duplicates": sum(1 for row in preview_rows if row.status == "duplicate"),
                "failed_count": len(errors),
            },
            "created_people": created_people,
            "errors": errors,
        }

    async def _resolve_tag_names(
        self, workspace_id: uuid.UUID, names: list[str]
    ) -> list[uuid.UUID]:
        normalized = list(dict.fromkeys(name.strip() for name in names if name.strip()))
        if not normalized:
            return []
        result = await self.db.execute(
            select(Tag).where(Tag.workspace_id == workspace_id, Tag.name.in_(normalized))
        )
        tags_by_name = {tag.name: tag for tag in result.scalars().all()}
        for name in normalized:
            if name not in tags_by_name:
                tag = Tag(workspace_id=workspace_id, name=name)
                self.db.add(tag)
                await self.db.flush()
                tags_by_name[name] = tag
        return [tags_by_name[name].id for name in normalized]

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
            normalize_linkedin_url((row.get("linkedin_url") or "").strip()) for row in rows
        ]
        existing_urls = await self._existing_urls(
            workspace_id,
            [result[0] for result in normalized_urls if result],
        )
        seen_urls: set[str] = set()
        preview_rows: list[ImportPreviewRow] = []

        for index, row in enumerate(rows, start=2):
            errors: list[str] = []
            first_name = self._clean(row.get("first_name"))
            last_name = self._clean(row.get("last_name"))
            name = (
                self._clean(row.get("name"))
                or " ".join(part for part in (first_name, last_name) if part)
                or None
            )
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
            processed_at_millis = self._parse_millis(
                row.get("processed_at_millis"), "processed_at_millis", errors
            )
            invite_accepted_at_millis = self._parse_millis(
                row.get("invite_accepted_at_millis"), "invite_accepted_at_millis", errors
            )
            processed_at = self._parse_octopus_datetime(
                row.get("processed_at"), processed_at_millis, "processed_at", errors
            )
            invite_accepted_at = self._parse_octopus_datetime(
                row.get("invite_accepted_at"),
                invite_accepted_at_millis,
                "invite_accepted_at",
                errors,
            )

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
                    first_name=first_name,
                    last_name=last_name,
                    linkedin_url=linkedin_url,
                    normalized_profile_url=normalized_url,
                    errors=errors,
                    current_role=self._clean(row.get("current_role")),
                    current_company=self._clean(row.get("current_company")),
                    location=self._clean(row.get("location")),
                    email=self._clean(row.get("email")),
                    phone_number=self._clean(row.get("phone_number")),
                    premium=self._parse_bool(row.get("premium"), errors),
                    company_website=self._clean(row.get("company_website")),
                    processed_at=processed_at,
                    processed_at_millis=processed_at_millis,
                    invite_accepted_at=invite_accepted_at,
                    invite_accepted_at_millis=invite_accepted_at_millis,
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

    def _parse_millis(self, value: Any, field: str, errors: list[str]) -> int | None:
        text = self._clean(value)
        if not text:
            return None
        try:
            return int(text)
        except ValueError:
            errors.append(f"{field} must be an integer")
            return None

    def _parse_octopus_datetime(
        self, value: Any, millis: int | None, field: str, errors: list[str]
    ) -> datetime | None:
        if millis is not None:
            try:
                return datetime.fromtimestamp(millis / 1000, tz=timezone.utc)
            except (OverflowError, OSError, ValueError):
                errors.append(f"{field}_millis is outside the supported date range")
                return None
        text = self._clean(value)
        if not text:
            return None
        try:
            return datetime.strptime(text, "%b %d, %Y %I:%M %p").replace(tzinfo=timezone.utc)
        except ValueError:
            errors.append(f"{field} must match 'Jul 06, 2026 11:06 PM'")
            return None

    def _parse_bool(self, value: Any, errors: list[str]) -> bool | None:
        text = self._clean(value)
        if not text:
            return None
        normalized = text.lower()
        if normalized in {"true", "yes", "1", "premium"}:
            return True
        if normalized in {"false", "no", "0"}:
            return False
        errors.append("premium must be true/false, yes/no, or 1/0")
        return None
