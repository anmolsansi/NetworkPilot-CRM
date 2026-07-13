import logging
import uuid
from datetime import date, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.core.logging import mask_id
from app.models.person import Person
from app.models.tag import Tag
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
        existing = await self._find_by_url(workspace_id, normalized_url) if check_duplicate else None
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
        )
        
        if data.tag_ids:
            tags_result = await self.db.execute(
                select(Tag).where(Tag.id.in_(data.tag_ids), Tag.workspace_id == workspace_id)
            )
            person.tags = list(tags_result.scalars().all())

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
        company: str | None = None,
        role: str | None = None,
        email: str | None = None,
        location: str | None = None,
        premium: bool | None = None,
        processed_from: datetime | None = None,
        processed_to: datetime | None = None,
        favorite: bool | None = None,
        favorite_notes: str | None = None,
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
                    Person.email.ilike(search_pattern),
                    Person.location.ilike(search_pattern),
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
            if field == "tag_ids":
                if value is not None:
                    tags_result = await self.db.execute(
                        select(Tag).where(Tag.id.in_(value), Tag.workspace_id == workspace_id)
                    )
                    person.tags = list(tags_result.scalars().all())
                else:
                    person.tags = []
            else:
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
