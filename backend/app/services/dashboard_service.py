import logging
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.import_job import ImportJob
from app.models.person import Person
from app.models.person_tag import PersonTag
from app.models.tag import Tag
from app.models.task import Task
from app.schemas.dashboard import (
    DashboardImportWidget,
    DashboardPersonWidget,
    DashboardSummary,
    DashboardTaskWidget,
    DashboardWidgets,
    DuePersonCard,
    TagDashboardSection,
)

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_summary(self, workspace_id: uuid.UUID) -> DashboardSummary:
        """Get dashboard summary counts."""
        base_query = select(Person).where(
            Person.workspace_id == workspace_id,
            Person.status == "active",
            Person.deleted_at.is_(None),
        )

        # Due today
        due_today_result = await self.db.execute(
            select(func.count()).select_from(
                base_query.where(Person.next_action_date == date.today()).subquery()
            )
        )
        due_today = due_today_result.scalar()

        # Overdue
        overdue_result = await self.db.execute(
            select(func.count()).select_from(
                base_query.where(Person.next_action_date < date.today()).subquery()
            )
        )
        overdue = overdue_result.scalar()

        # Waiting for reply
        waiting_result = await self.db.execute(
            select(func.count()).select_from(
                base_query.where(Person.stage == "waiting_for_reply").subquery()
            )
        )
        waiting_for_reply = waiting_result.scalar()

        # Active total
        active_result = await self.db.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        active_total = active_result.scalar()

        return DashboardSummary(
            due_today=due_today,
            overdue=overdue,
            waiting_for_reply=waiting_for_reply,
            active_total=active_total,
        )

    async def get_due(
        self,
        workspace_id: uuid.UUID,
        target_date: date | None = None,
        include_overdue: bool = True,
        priority: str | None = None,
    ) -> list[DuePersonCard]:
        """Get people due for follow-up."""
        if target_date is None:
            target_date = date.today()

        query = select(Person).where(
            Person.workspace_id == workspace_id,
            Person.status == "active",
            Person.deleted_at.is_(None),
            Person.next_action_date.isnot(None),
        )

        # Filter by date
        if include_overdue:
            query = query.where(Person.next_action_date <= target_date)
        else:
            query = query.where(Person.next_action_date == target_date)

        # Filter by priority
        if priority:
            query = query.where(Person.priority == priority)

        # Order by priority and date
        query = query.order_by(Person.next_action_date, Person.priority)

        result = await self.db.execute(query)
        people = result.scalars().all()

        return [
            DuePersonCard(
                id=p.id,
                name=p.name,
                company=p.company,
                role=p.role,
                linkedin_url=p.linkedin_url,
                stage=p.stage,
                priority=p.priority,
                next_action_type=p.next_action_type,
                next_action_date=p.next_action_date,
                last_action_type=p.last_action_type,
            )
            for p in people
        ]

    async def get_tag_sections(self, workspace_id: uuid.UUID) -> list[TagDashboardSection]:
        result = await self.db.execute(
            select(Tag, func.count(Person.id))
            .outerjoin(PersonTag, PersonTag.tag_id == Tag.id)
            .outerjoin(
                Person,
                (Person.id == PersonTag.person_id) & (Person.deleted_at.is_(None)),
            )
            .where(Tag.workspace_id == workspace_id)
            .group_by(Tag.id)
            .order_by(func.count(Person.id).desc(), Tag.name.asc())
        )
        return [
            TagDashboardSection(
                id=tag.id,
                name=tag.name,
                color=tag.color,
                people_count=count,
            )
            for tag, count in result.all()
        ]

    async def get_widgets(self, workspace_id: uuid.UUID, limit: int = 20) -> DashboardWidgets:
        """Load all configurable dashboard widget datasets with workspace scoping."""
        favourites = (
            await self.db.scalars(
                select(Person)
                .where(
                    Person.workspace_id == workspace_id,
                    Person.deleted_at.is_(None),
                    Person.is_favorite.is_(True),
                )
                .order_by(Person.updated_at.desc())
                .limit(limit)
            )
        ).all()

        accepted_rows = (
            await self.db.execute(
                select(Person, func.max(Activity.created_at).label("accepted_at"))
                .join(Activity, Activity.person_id == Person.id)
                .where(
                    Person.workspace_id == workspace_id,
                    Person.deleted_at.is_(None),
                    Activity.workspace_id == workspace_id,
                    Activity.action_type == "accepted",
                    Activity.deleted_at.is_(None),
                    Activity.created_at >= datetime.now(timezone.utc) - timedelta(days=14),
                )
                .group_by(Person.id)
                .order_by(func.max(Activity.created_at).desc())
                .limit(limit)
            )
        ).all()

        stale_cutoff = date.today() - timedelta(days=30)
        stale = (
            await self.db.scalars(
                select(Person)
                .where(
                    Person.workspace_id == workspace_id,
                    Person.deleted_at.is_(None),
                    Person.status == "active",
                    (Person.last_action_date < stale_cutoff)
                    | (
                        Person.last_action_date.is_(None)
                        & (
                            Person.created_at
                            < datetime.combine(
                                stale_cutoff, datetime.min.time(), tzinfo=timezone.utc
                            )
                        )
                    ),
                )
                .order_by(Person.last_action_date.asc().nullsfirst(), Person.created_at.asc())
                .limit(limit)
            )
        ).all()

        overdue_rows = (
            await self.db.execute(
                select(Task, Person.name)
                .join(Person, Person.id == Task.person_id)
                .where(
                    Task.workspace_id == workspace_id,
                    Task.status != "completed",
                    Task.due_date < date.today(),
                    Person.workspace_id == workspace_id,
                    Person.deleted_at.is_(None),
                )
                .order_by(Task.due_date.asc())
                .limit(limit)
            )
        ).all()

        imports = (
            await self.db.scalars(
                select(ImportJob)
                .where(ImportJob.workspace_id == workspace_id)
                .order_by(ImportJob.created_at.desc())
                .limit(limit)
            )
        ).all()

        def person_card(person: Person, occurred_at=None):
            return DashboardPersonWidget(
                id=person.id,
                name=person.name,
                company=person.company,
                role=person.role,
                stage=person.stage,
                occurred_at=occurred_at,
            )

        return DashboardWidgets(
            favourites=[person_card(person) for person in favourites],
            newly_accepted=[
                person_card(person, accepted_at) for person, accepted_at in accepted_rows
            ],
            stale_relationships=[person_card(person, person.last_action_date) for person in stale],
            overdue_tasks=[
                DashboardTaskWidget(
                    id=task.id,
                    person_id=task.person_id,
                    person_name=person_name,
                    title=task.title,
                    due_date=task.due_date,
                )
                for task, person_name in overdue_rows
            ],
            recent_imports=[
                DashboardImportWidget(
                    id=job.id,
                    file_name=job.file_name,
                    status=job.status,
                    total_rows=job.total_rows,
                    failed_rows=job.failed_rows,
                    created_at=job.created_at,
                )
                for job in imports
            ],
        )
