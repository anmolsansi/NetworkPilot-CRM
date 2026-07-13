import uuid
import json
from datetime import datetime
from typing import List, Dict, Any

from sqlalchemy import select, or_, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import AppError, ErrorCode
from app.models.person import Person
from app.models.activity import Activity
from app.models.person_merge import PersonMerge
from app.schemas.duplicates import DuplicateGroup

class DuplicateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_duplicates(self, workspace_id: uuid.UUID) -> List[DuplicateGroup]:
        # Simple duplicate detection: group by first_name + last_name
        stmt = (
            select(Person)
            .where(Person.workspace_id == workspace_id)
            .where(Person.deleted_at.is_(None))
        )
        result = await self.db.execute(stmt)
        people = result.scalars().all()

        groups: Dict[str, List[Person]] = {}
        for p in people:
            # Normalize key
            name_key = f"{p.first_name.strip().lower()} {p.last_name.strip().lower()}"
            if name_key not in groups:
                groups[name_key] = []
            groups[name_key].append(p)

        # Also group by email if available and not empty
        email_groups: Dict[str, List[Person]] = {}
        for p in people:
            if p.email and p.email.strip():
                email_key = p.email.strip().lower()
                if email_key not in email_groups:
                    email_groups[email_key] = []
                email_groups[email_key].append(p)

        # Merge groups that have > 1 person
        duplicate_groups = []
        for key, p_list in groups.items():
            if len(p_list) > 1:
                duplicate_groups.append(DuplicateGroup(
                    group_id=f"name:{key}",
                    people=[self._person_to_dict(p) for p in p_list]
                ))
        
        for key, p_list in email_groups.items():
            if len(p_list) > 1:
                duplicate_groups.append(DuplicateGroup(
                    group_id=f"email:{key}",
                    people=[self._person_to_dict(p) for p in p_list]
                ))

        # Deduplicate groups by person IDs (naive)
        seen_combinations = set()
        final_groups = []
        for g in duplicate_groups:
            p_ids = tuple(sorted([p["id"] for p in g.people]))
            if p_ids not in seen_combinations:
                seen_combinations.add(p_ids)
                final_groups.append(g)

        return final_groups

    def _person_to_dict(self, p: Person) -> Dict[str, Any]:
        return {
            "id": str(p.id),
            "first_name": p.first_name,
            "last_name": p.last_name,
            "headline": p.headline,
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
        fields_to_keep_from_source: List[str]
    ) -> Dict[str, Any]:
        if target_person_id == source_person_id:
            raise AppError(ErrorCode.VALIDATION_ERROR, "Target and source cannot be the same")

        target_stmt = select(Person).where(
            Person.id == target_person_id,
            Person.workspace_id == workspace_id,
            Person.deleted_at.is_(None)
        )
        source_stmt = select(Person).where(
            Person.id == source_person_id,
            Person.workspace_id == workspace_id,
            Person.deleted_at.is_(None)
        )

        target_person = (await self.db.execute(target_stmt)).scalar_one_or_none()
        source_person = (await self.db.execute(source_stmt)).scalar_one_or_none()

        if not target_person or not source_person:
            raise AppError(ErrorCode.NOT_FOUND, "Target or source person not found")

        # Keep requested fields
        merge_data = {}
        for field in fields_to_keep_from_source:
            if hasattr(source_person, field) and hasattr(target_person, field):
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
            .where(Activity.person_id == source_person_id)
            .values(person_id=target_person_id)
        )

        # Soft delete source
        source_person.deleted_at = datetime.utcnow()

        # Record merge audit
        person_merge = PersonMerge(
            workspace_id=workspace_id,
            target_person_id=target_person_id,
            source_person_id=source_person_id,
            merged_by_user_id=user_id,
            merge_data=merge_data
        )
        self.db.add(person_merge)

        await self.db.commit()
        await self.db.refresh(target_person)

        return self._person_to_dict(target_person)
