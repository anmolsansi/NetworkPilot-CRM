import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundError, ValidationError
from app.models.activity import Activity
from app.models.person import Person
from app.models.person_merge import PersonMerge
from app.schemas.duplicates import DuplicateGroup


class DuplicateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_duplicates(self, workspace_id: uuid.UUID) -> List[DuplicateGroup]:
        stmt = (
            select(Person)
            .where(Person.workspace_id == workspace_id)
            .where(Person.deleted_at.is_(None))
            .options(selectinload(Person.tags))
        )
        result = await self.db.execute(stmt)
        people = result.scalars().all()

        candidates: Dict[str, List[Person]] = {}
        for p in people:
            keys: list[str] = []
            if p.linkedin_url:
                keys.append(f"linkedin:{p.linkedin_url.strip().lower().rstrip('/')}")
            if p.email and p.email.strip():
                keys.append(f"email:{p.email.strip().lower()}")
            name = " ".join(
                part.strip().lower()
                for part in (p.first_name, p.last_name)
                if part and part.strip()
            )
            if not name:
                name = (p.name or "").strip().lower()
            company = (p.company or "").strip().lower()
            if name and company:
                keys.append(f"name_company:{name}|{company}")
            for key in keys:
                candidates.setdefault(key, []).append(p)

        duplicate_groups: list[DuplicateGroup] = []
        seen: set[tuple[str, ...]] = set()
        for key, group in candidates.items():
            ids = tuple(sorted(str(person.id) for person in group))
            if len(ids) < 2 or ids in seen:
                continue
            seen.add(ids)
            duplicate_groups.append(
                DuplicateGroup(group_id=key, people=[self._person_to_dict(p) for p in group])
            )
        return duplicate_groups

    def _person_to_dict(self, p: Person) -> Dict[str, Any]:
        return {
            "id": str(p.id),
            "first_name": p.first_name,
            "last_name": p.last_name,
            "name": p.name,
            "role": p.role,
            "company": p.company,
            "email": p.email,
            "linkedin_url": p.linkedin_url,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }

    async def merge_people(
        self,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
        target_person_id: uuid.UUID,
        source_person_id: uuid.UUID,
        fields_to_keep_from_source: List[str],
    ) -> Dict[str, Any]:
        if target_person_id == source_person_id:
            raise ValidationError("Target and source cannot be the same")

        target_stmt = (
            select(Person)
            .where(
                Person.id == target_person_id,
                Person.workspace_id == workspace_id,
                Person.deleted_at.is_(None),
            )
            .options(selectinload(Person.tags))
        )
        source_stmt = (
            select(Person)
            .where(
                Person.id == source_person_id,
                Person.workspace_id == workspace_id,
                Person.deleted_at.is_(None),
            )
            .options(selectinload(Person.tags))
        )

        target_person = (await self.db.execute(target_stmt)).scalar_one_or_none()
        source_person = (await self.db.execute(source_stmt)).scalar_one_or_none()

        if not target_person or not source_person:
            raise NotFoundError("Person", "Target or source")

        # Keep requested fields
        merge_data = {}
        for field in fields_to_keep_from_source:
            val = getattr(source_person, field)
            setattr(target_person, field, val)
            merge_data[field] = val

        # Add tags from source
        if source_person.tags:
            target_tags = set(target_person.tags) if target_person.tags else set()
            for tag in source_person.tags:
                target_tags.add(tag)
            target_person.tags = list(target_tags)

        # Move activities
        await self.db.execute(
            update(Activity)
            .where(
                Activity.person_id == source_person_id,
                Activity.workspace_id == workspace_id,
            )
            .values(person_id=target_person_id)
        )

        # Soft delete source
        source_person.deleted_at = datetime.now(timezone.utc)

        # Record merge audit
        person_merge = PersonMerge(
            workspace_id=workspace_id,
            target_person_id=target_person_id,
            source_person_id=source_person_id,
            merged_by_user_id=user_id,
            merge_data=merge_data,
        )
        self.db.add(person_merge)

        await self.db.flush()

        return self._person_to_dict(target_person)
