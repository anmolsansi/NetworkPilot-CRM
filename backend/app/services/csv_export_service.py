import uuid
from datetime import date

from sqlalchemy import exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.person import Person
from app.schemas.exports import PeopleExportFilters
from app.services.csv_sanitizer import write_csv

DEFAULT_EXPORT_FIELDS = [
    "name",
    "linkedin_url",
    "current_role",
    "current_company",
    "location",
    "priority",
    "stage",
    "status",
    "next_action_type",
    "next_action_date",
    "last_action_type",
    "last_action_at",
    "follow_up_count",
    "tags",
]

PRIVATE_FIELDS = ["connection_note", "conversation_context"]


class CsvExportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def export_people(self, filters: PeopleExportFilters) -> str:
        people = await self._fetch_people(filters)
        follow_up_counts = await self._follow_up_counts(
            filters.workspace_id,
            [person.id for person in people],
        )
        headers = DEFAULT_EXPORT_FIELDS + (PRIVATE_FIELDS if filters.include_private_notes else [])
        rows = [
            self._person_row(
                person,
                follow_up_counts.get(person.id, 0),
                filters.include_private_notes,
            )
            for person in people
        ]
        return write_csv(headers, rows)

    async def _fetch_people(self, filters: PeopleExportFilters) -> list[Person]:
        query = select(Person).where(
            Person.workspace_id == filters.workspace_id,
            Person.deleted_at.is_(None),
        )

        if filters.stage:
            query = query.where(Person.stage == filters.stage)
        if filters.status:
            query = query.where(Person.status == filters.status)
        if filters.priority:
            query = query.where(Person.priority == filters.priority)
        if filters.next_action_type:
            query = query.where(Person.next_action_type == filters.next_action_type)
        if filters.accepted_only:
            query = query.where(
                exists().where(
                    Activity.person_id == Person.id,
                    Activity.workspace_id == filters.workspace_id,
                    Activity.action_type == "accepted",
                )
            )
        if filters.due == "today":
            query = query.where(Person.next_action_date <= date.today(), Person.status == "active")
        elif filters.due == "overdue":
            query = query.where(Person.next_action_date < date.today(), Person.status == "active")
        if filters.date_from:
            query = query.where(Person.next_action_date >= filters.date_from)
        if filters.date_to:
            query = query.where(Person.next_action_date <= filters.date_to)
        if filters.company:
            query = query.where(Person.company.ilike(f"%{filters.company}%"))
        if filters.role:
            query = query.where(Person.role.ilike(f"%{filters.role}%"))
        if filters.tags:
            tags = [tag.strip() for tag in filters.tags.split(",") if tag.strip()]
            if tags:
                query = query.where(or_(*(Person.tags.any(tag) for tag in tags)))

        result = await self.db.execute(query.order_by(Person.created_at.desc()))
        return list(result.scalars().all())

    async def _follow_up_counts(
        self,
        workspace_id: uuid.UUID,
        person_ids: list[uuid.UUID],
    ) -> dict[uuid.UUID, int]:
        if not person_ids:
            return {}
        result = await self.db.execute(
            select(Activity.person_id, func.count(Activity.id))
            .where(
                Activity.workspace_id == workspace_id,
                Activity.person_id.in_(person_ids),
                Activity.action_type.in_(["follow_up_1_sent", "follow_up_2_sent"]),
            )
            .group_by(Activity.person_id)
        )
        return {person_id: count for person_id, count in result.all()}

    def _person_row(
        self,
        person: Person,
        follow_up_count: int,
        include_private_notes: bool,
    ) -> dict[str, object]:
        row: dict[str, object] = {
            "name": person.name,
            "linkedin_url": person.linkedin_url,
            "current_role": person.role,
            "current_company": person.company,
            "location": person.location,
            "priority": person.priority,
            "stage": person.stage,
            "status": person.status,
            "next_action_type": person.next_action_type,
            "next_action_date": person.next_action_date,
            "last_action_type": person.last_action_type,
            "last_action_at": person.last_action_date,
            "follow_up_count": follow_up_count,
            "tags": person.tags or [],
        }
        if include_private_notes:
            row["connection_note"] = person.connection_note
            row["conversation_context"] = person.notes
        return row
