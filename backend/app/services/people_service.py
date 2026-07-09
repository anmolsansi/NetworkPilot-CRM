import logging
import uuid
from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.core.logging import mask_id
from app.models.person import Person
from app.schemas.people import PersonCreate, PersonUpdate
from app.services.url_normalizer import normalize_linkedin_url

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)


class PeopleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, workspace_id: uuid.UUID, data: PersonCreate) -> Person:
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
        existing = await self._find_by_url(workspace_id, normalized_url)
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

        person = Person(
            workspace_id=workspace_id,
            name=data.name,
            linkedin_url=normalized_url,
            linkedin_slug=slug,
            role=data.role,
            company=data.company,
            location=data.location,
            priority=data.priority,
            connection_note=data.connection_note,
            notes=data.notes,
            tags=data.tags,
            stage="invite_sent",
            status="active",
        )

        self.db.add(person)
        await self.db.flush()
        _module_logger.info(
            "people_service.create.completed workspace_id=%s person_id=%s slug=%s",
            mask_id(str(workspace_id)),
            mask_id(str(person.id)),
            slug,
        )
        return person

    async def get(self, workspace_id: uuid.UUID, person_id: uuid.UUID) -> Person:
        """Get a person by ID within workspace."""
        _module_logger.debug(
            "people_service.get.started workspace_id=%s person_id=%s",
            mask_id(str(workspace_id)),
            mask_id(str(person_id)),
        )
        result = await self.db.execute(
            select(Person).where(
                Person.id == person_id,
                Person.workspace_id == workspace_id,
                Person.deleted_at.is_(None),
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
        priority: str | None = None,
        status: str | None = None,
        search: str | None = None,
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
        query = select(Person).where(
            Person.workspace_id == workspace_id,
            Person.deleted_at.is_(None),
        )

        # Apply filters
        if stage:
            query = query.where(Person.stage == stage)
        if priority:
            query = query.where(Person.priority == priority)
        if status:
            query = query.where(Person.status == status)
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Person.name.ilike(search_pattern),
                    Person.company.ilike(search_pattern),
                    Person.role.ilike(search_pattern),
                )
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Paginate
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit).order_by(Person.created_at.desc())

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
        self, workspace_id: uuid.UUID, person_id: uuid.UUID, data: PersonUpdate
    ) -> Person:
        """Update person profile fields."""
        person = await self.get(workspace_id, person_id)

        update_data = data.model_dump(exclude_unset=True)
        _module_logger.info(
            "people_service.update.started workspace_id=%s person_id=%s fields=%s",
            mask_id(str(workspace_id)),
            mask_id(str(person_id)),
            sorted(update_data.keys()),
        )
        for field, value in update_data.items():
            setattr(person, field, value)

        await self.db.flush()
        _module_logger.info(
            "people_service.update.completed workspace_id=%s person_id=%s",
            mask_id(str(workspace_id)),
            mask_id(str(person.id)),
        )
        return person

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
        return person

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
        return person

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
