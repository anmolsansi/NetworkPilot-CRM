from __future__ import annotations

import logging
import uuid
from datetime import date, datetime

from sqlalchemy import Text, cast, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.core.logging import mask_id
from app.models.activity import Activity
from app.models.custom_field import CustomField
from app.models.person import Person
from app.models.pipeline_stage import PipelineStage
from app.models.tag import Tag
from app.models.workspace import WorkspaceMember
from app.schemas.people import PersonCreate, PersonUpdate
from app.services.url_normalizer import normalize_linkedin_url

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)


class PeopleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        workspace_id: uuid.UUID,
        data: PersonCreate,
        *,
        check_duplicate: bool = True,
        resolved_tags: list[Tag] | None = None,
        reload: bool = True,
    ) -> Person:
        """Create a person with URL normalization and duplicate detection."""
        _module_logger.info(
            "people_service.create.started workspace_id=%s priority=%s url_present=%s",
            mask_id(str(workspace_id)),
            data.priority,
            bool(data.linkedin_url),
        )
        result = normalize_linkedin_url(data.linkedin_url)
        if not result:
            _module_logger.warning(
                "people_service.create.invalid_linkedin_url workspace_id=%s",
                mask_id(str(workspace_id)),
            )
            raise ValidationError("Invalid LinkedIn profile URL")

        normalized_url, slug = result

        # Check for duplicate
        existing = (
            await self._find_by_url(workspace_id, normalized_url) if check_duplicate else None
        )
        if existing:
            _module_logger.warning(
                "people_service.create.duplicate workspace_id=%s existing_person_id=%s",
                mask_id(str(workspace_id)),
                mask_id(str(existing.id)),
            )
            raise ConflictError(
                "A person with this LinkedIn profile already exists",
                details={"person_id": str(existing.id), "name": existing.name},
            )

        custom_fields_data = await self._validate_custom_fields(
            workspace_id, data.custom_fields_data or {}
        )
        person = Person(
            workspace_id=workspace_id,
            name=data.name,
            first_name=data.first_name,
            last_name=data.last_name,
            linkedin_url=normalized_url,
            linkedin_slug=slug,
            role=data.role,
            company=data.company,
            location=data.location,
            email=data.email,
            phone_number=data.phone_number,
            premium=data.premium,
            company_website=data.company_website,
            processed_at=data.processed_at,
            processed_at_millis=data.processed_at_millis,
            invite_accepted_at=data.invite_accepted_at,
            invite_accepted_at_millis=data.invite_accepted_at_millis,
            is_favorite=data.is_favorite,
            favorite_notes=data.favorite_notes,
            priority=data.priority,
            connection_note=data.connection_note,
            notes=data.notes,
            stage="invite_sent",
            status="active",
            custom_fields_data=custom_fields_data,
            stage_id=data.stage_id,
            owner_id=data.owner_id,
        )

        if data.tag_ids:
            person.tags = (
                self._validate_resolved_tags(workspace_id, data.tag_ids, resolved_tags)
                if resolved_tags is not None
                else await self._resolve_tags(workspace_id, data.tag_ids)
            )
        if data.stage_id:
            await self._require_pipeline_stage(workspace_id, data.stage_id)
        if data.owner_id:
            await self._require_workspace_member(workspace_id, data.owner_id)

        self.db.add(person)
        await self.db.flush()
        _module_logger.info(
            "people_service.create.completed workspace_id=%s person_id=%s slug=%s",
            mask_id(str(workspace_id)),
            mask_id(str(person.id)),
            slug,
        )
        return await self.get(workspace_id, person.id) if reload else person

    async def get(self, workspace_id: uuid.UUID, person_id: uuid.UUID) -> Person:
        """Get a person by ID within workspace."""
        _module_logger.debug(
            "people_service.get.started workspace_id=%s person_id=%s",
            mask_id(str(workspace_id)),
            mask_id(str(person_id)),
        )
        result = await self.db.execute(
            select(Person)
            .where(
                Person.id == person_id,
                Person.workspace_id == workspace_id,
                Person.deleted_at.is_(None),
            )
            .options(
                selectinload(Person.tags),
                selectinload(Person.pipeline_stage),
                selectinload(Person.owner),
            )
        )
        person = result.scalar_one_or_none()
        if not person:
            _module_logger.warning(
                "people_service.get.missing workspace_id=%s person_id=%s",
                mask_id(str(workspace_id)),
                mask_id(str(person_id)),
            )
            raise NotFoundError("Person", str(person_id))
        return person

    async def list(
        self,
        workspace_id: uuid.UUID,
        stage: str | None = None,
        stage_id: uuid.UUID | None = None,
        tag_ids: list[uuid.UUID] | None = None,
        owner_id: uuid.UUID | None = None,
        priority: str | None = None,
        status: str | None = None,
        search: str | None = None,
        company: str | None = None,
        role: str | None = None,
        email: str | None = None,
        location: str | None = None,
        premium: bool | None = None,
        processed_from: datetime | None = None,
        processed_to: datetime | None = None,
        favorite: bool | None = None,
        favorite_notes: str | None = None,
        include_deleted: bool = False,
        deleted_only: bool = False,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        limit: int = 50,
    ) -> tuple[list[Person], int]:
        """List people in workspace with filters."""
        _module_logger.info(
            "people_service.list.started workspace_id=%s page=%s limit=%s has_search=%s",
            mask_id(str(workspace_id)),
            page,
            limit,
            bool(search),
        )
        query = (
            select(Person)
            .where(
                Person.workspace_id == workspace_id,
            )
            .options(
                selectinload(Person.tags),
                selectinload(Person.pipeline_stage),
                selectinload(Person.owner),
            )
        )
        if deleted_only:
            query = query.where(Person.deleted_at.is_not(None))
        elif not include_deleted:
            query = query.where(Person.deleted_at.is_(None))

        # Apply filters
        if stage:
            query = query.where(Person.stage == stage)
        if stage_id:
            query = query.where(Person.stage_id == stage_id)
        if tag_ids:
            for t_id in tag_ids:
                query = query.where(Person.tags.any(Tag.id == t_id))
        if owner_id:
            query = query.where(Person.owner_id == owner_id)
        if priority:
            query = query.where(Person.priority == priority)
        if status:
            query = query.where(Person.status == status)
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Person.name.ilike(search_pattern),
                    Person.first_name.ilike(search_pattern),
                    Person.last_name.ilike(search_pattern),
                    Person.company.ilike(search_pattern),
                    Person.role.ilike(search_pattern),
                    Person.email.ilike(search_pattern),
                    Person.location.ilike(search_pattern),
                    Person.phone_number.ilike(search_pattern),
                    Person.company_website.ilike(search_pattern),
                    Person.favorite_notes.ilike(search_pattern),
                    Person.notes.ilike(search_pattern),
                    Person.connection_note.ilike(search_pattern),
                    Person.stage.ilike(search_pattern),
                    Person.status.ilike(search_pattern),
                    Person.priority.ilike(search_pattern),
                    cast(Person.custom_fields_data, Text).ilike(search_pattern),
                    cast(Person.processed_at, Text).ilike(search_pattern),
                    cast(Person.invite_accepted_at, Text).ilike(search_pattern),
                    cast(Person.next_action_date, Text).ilike(search_pattern),
                    cast(Person.last_action_date, Text).ilike(search_pattern),
                    Person.tags.any(Tag.name.ilike(search_pattern)),
                    exists().where(
                        Activity.person_id == Person.id,
                        Activity.workspace_id == workspace_id,
                        Activity.deleted_at.is_(None),
                        or_(
                            Activity.message.ilike(search_pattern),
                            Activity.notes.ilike(search_pattern),
                        ),
                    ),
                )
            )
        if company:
            query = query.where(Person.company.ilike(f"%{company}%"))
        if role:
            query = query.where(Person.role.ilike(f"%{role}%"))
        if email:
            query = query.where(Person.email.ilike(f"%{email}%"))
        if location:
            query = query.where(Person.location.ilike(f"%{location}%"))
        if premium is not None:
            query = query.where(Person.premium == premium)
        if processed_from:
            query = query.where(Person.processed_at >= processed_from)
        if processed_to:
            query = query.where(Person.processed_at <= processed_to)
        if favorite is not None:
            query = query.where(Person.is_favorite == favorite)
        if favorite_notes:
            query = query.where(Person.favorite_notes.ilike(f"%{favorite_notes}%"))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Paginate
        offset = (page - 1) * limit
        sort_columns = {
            "linkedin_url": Person.linkedin_url,
            "first_name": Person.first_name,
            "last_name": Person.last_name,
            "company": Person.company,
            "role": Person.role,
            "email": Person.email,
            "phone_number": Person.phone_number,
            "premium": Person.premium,
            "location": Person.location,
            "company_website": Person.company_website,
            "processed_at": Person.processed_at,
            "processed_at_millis": Person.processed_at_millis,
            "invite_accepted_at": Person.invite_accepted_at,
            "invite_accepted_at_millis": Person.invite_accepted_at_millis,
            "created_at": Person.created_at,
            "is_favorite": Person.is_favorite,
            "favorite_notes": Person.favorite_notes,
        }
        sort_column = sort_columns.get(sort_by, Person.created_at)
        ordering = sort_column.asc() if sort_order == "asc" else sort_column.desc()
        query = query.offset(offset).limit(limit).order_by(ordering.nullslast(), Person.id.asc())

        result = await self.db.execute(query)
        people = result.scalars().all()
        _module_logger.info(
            "people_service.list.completed workspace_id=%s count=%s total=%s",
            mask_id(str(workspace_id)),
            len(people),
            total,
        )
        return people, total

    async def update(
        self,
        workspace_id: uuid.UUID,
        person_id: uuid.UUID,
        data: PersonUpdate,
        *,
        resolved_tags: list[Tag] | None = None,
        reload: bool = True,
    ) -> Person:
        """Update person profile fields."""
        person = await self.get(workspace_id, person_id)

        update_data = data.model_dump(exclude_unset=True)
        if "custom_fields_data" in update_data:
            update_data["custom_fields_data"] = await self._validate_custom_fields(
                workspace_id, update_data["custom_fields_data"] or {}
            )
        _module_logger.info(
            "people_service.update.started workspace_id=%s person_id=%s fields=%s",
            mask_id(str(workspace_id)),
            mask_id(str(person_id)),
            sorted(update_data.keys()),
        )
        for field, value in update_data.items():
            if field == "tag_ids":
                tag_ids = value or []
                person.tags = (
                    self._validate_resolved_tags(workspace_id, tag_ids, resolved_tags)
                    if resolved_tags is not None
                    else await self._resolve_tags(workspace_id, tag_ids)
                )
            elif field == "stage_id":
                if value is not None:
                    await self._require_pipeline_stage(workspace_id, value)
                    if (
                        person.pipeline_stage
                        and person.pipeline_stage.allowed_next_stage_ids
                        and str(value) not in person.pipeline_stage.allowed_next_stage_ids
                    ):
                        raise ValidationError("This pipeline stage transition is not allowed.")
                person.stage_id = value
            elif field == "owner_id":
                if value is not None:
                    await self._require_workspace_member(workspace_id, value)
                person.owner_id = value
            else:
                setattr(person, field, value)

        await self.db.flush()
        if "manual_warmth" in update_data:
            from app.services.relationship_service import RelationshipService

            await RelationshipService(self.db).recalculate_freshness(workspace_id, person_id)
        _module_logger.info(
            "people_service.update.completed workspace_id=%s person_id=%s",
            mask_id(str(workspace_id)),
            mask_id(str(person.id)),
        )
        return await self.get(workspace_id, person.id) if reload else person

    @staticmethod
    def _validate_resolved_tags(
        workspace_id: uuid.UUID,
        tag_ids: list[uuid.UUID],
        resolved_tags: list[Tag],
    ) -> list[Tag]:
        """Validate caller-provided tags without issuing another database query."""
        if {tag.id for tag in resolved_tags} != set(tag_ids) or any(
            tag.workspace_id != workspace_id for tag in resolved_tags
        ):
            raise ValidationError("One or more tags do not belong to this workspace.")
        return resolved_tags

    async def _resolve_tags(self, workspace_id: uuid.UUID, tag_ids: list[uuid.UUID]) -> list[Tag]:
        if not tag_ids:
            return []
        result = await self.db.execute(
            select(Tag).where(Tag.id.in_(tag_ids), Tag.workspace_id == workspace_id)
        )
        tags_by_id = {tag.id: tag for tag in result.scalars().all()}
        if len(tags_by_id) != len(tag_ids):
            raise ValidationError("One or more tags do not belong to this workspace.")
        return [tags_by_id[tag_id] for tag_id in tag_ids]

    async def _require_pipeline_stage(
        self, workspace_id: uuid.UUID, stage_id: uuid.UUID
    ) -> PipelineStage:
        result = await self.db.execute(
            select(PipelineStage).where(
                PipelineStage.id == stage_id,
                PipelineStage.workspace_id == workspace_id,
            )
        )
        stage = result.scalar_one_or_none()
        if stage is None:
            raise ValidationError("Pipeline stage does not belong to this workspace.")
        return stage

    async def _require_workspace_member(self, workspace_id: uuid.UUID, user_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.deleted_at.is_(None),
            )
        )
        member = result.scalar_one_or_none()
        if member is None:
            raise ValidationError("Owner must be an active member of this workspace.")

    async def _validate_custom_fields(
        self, workspace_id: uuid.UUID, values: dict
    ) -> dict[str, object]:
        if not values:
            return {}
        try:
            field_ids = [uuid.UUID(str(key)) for key in values]
        except (TypeError, ValueError) as exc:
            raise ValidationError("Custom field values must use field IDs as keys.") from exc
        result = await self.db.execute(
            select(CustomField).where(
                CustomField.workspace_id == workspace_id,
                CustomField.id.in_(field_ids),
            )
        )
        definitions = {str(field.id): field for field in result.scalars().all()}
        if len(definitions) != len(field_ids):
            raise ValidationError("One or more custom fields do not belong to this workspace.")

        normalized: dict[str, object] = {}
        for key, value in values.items():
            field = definitions[str(uuid.UUID(str(key)))]
            if value is None or value == "":
                continue
            valid = (
                (field.field_type == "text" and isinstance(value, str))
                or (
                    field.field_type == "number"
                    and isinstance(value, (int, float))
                    and not isinstance(value, bool)
                )
                or (field.field_type == "boolean" and isinstance(value, bool))
                or (
                    field.field_type == "date"
                    and isinstance(value, str)
                    and self._is_iso_date(value)
                )
                or (
                    field.field_type == "select"
                    and isinstance(value, str)
                    and value in (field.options or {}).get("choices", [])
                )
            )
            if not valid:
                raise ValidationError(f"Invalid value for custom field '{field.name}'.")
            normalized[str(field.id)] = value
        return normalized

    @staticmethod
    def _is_iso_date(value: str) -> bool:
        try:
            date.fromisoformat(value)
            return True
        except ValueError:
            return False

    async def soft_delete(self, workspace_id: uuid.UUID, person_id: uuid.UUID) -> None:
        """Soft delete a person."""
        person = await self.get(workspace_id, person_id)
        from datetime import datetime, timezone

        person.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
        _module_logger.info(
            "people_service.soft_delete.completed workspace_id=%s person_id=%s",
            mask_id(str(workspace_id)),
            mask_id(str(person_id)),
        )

    async def restore(self, workspace_id: uuid.UUID, person_id: uuid.UUID) -> Person:
        """Restore a soft deleted person."""
        result = await self.db.execute(
            select(Person).where(
                Person.id == person_id,
                Person.workspace_id == workspace_id,
            )
        )
        person = result.scalar_one_or_none()
        if not person:
            raise NotFoundError("Person", str(person_id))
        if person.deleted_at is None:
            raise ValidationError("Only deleted people can be restored.")

        person.deleted_at = None
        await self.db.flush()
        _module_logger.info(
            "people_service.restore.completed workspace_id=%s person_id=%s",
            mask_id(str(workspace_id)),
            mask_id(str(person_id)),
        )
        return await self.get(workspace_id, person.id)

    async def unarchive(self, workspace_id: uuid.UUID, person_id: uuid.UUID) -> Person:
        person = await self.get(workspace_id, person_id)
        if person.status != "archived" and person.stage != "archived":
            raise ValidationError("Only archived people can be unarchived.")
        person.status = "active"
        person.stage = "invite_sent"
        person.stage_id = None
        await self.db.flush()
        return await self.get(workspace_id, person.id)

    async def archive(self, workspace_id: uuid.UUID, person_id: uuid.UUID) -> Person:
        """Archive a person."""
        person = await self.get(workspace_id, person_id)
        person.status = "archived"
        person.stage = "archived"
        person.next_action_type = None
        person.next_action_date = None
        await self.db.flush()
        _module_logger.info(
            "people_service.archive.completed workspace_id=%s person_id=%s",
            mask_id(str(workspace_id)),
            mask_id(str(person.id)),
        )
        return await self.get(workspace_id, person.id)

    async def snooze(
        self, workspace_id: uuid.UUID, person_id: uuid.UUID, until_date: date
    ) -> Person:
        """Snooze a person by setting next_action_date."""
        person = await self.get(workspace_id, person_id)
        person.next_action_date = until_date
        person.next_action_type = "snoozed"
        await self.db.flush()
        _module_logger.info(
            "people_service.snooze.completed workspace_id=%s person_id=%s until_date=%s",
            mask_id(str(workspace_id)),
            mask_id(str(person.id)),
            until_date,
        )
        return await self.get(workspace_id, person.id)

    async def _find_by_url(self, workspace_id: uuid.UUID, url: str) -> Person | None:
        """Find a person by normalized URL in workspace."""
        _module_logger.debug(
            "people_service.find_by_url.started workspace_id=%s",
            mask_id(str(workspace_id)),
        )
        result = await self.db.execute(
            select(Person).where(
                Person.workspace_id == workspace_id,
                Person.linkedin_url == url,
                Person.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()
