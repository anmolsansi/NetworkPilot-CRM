import uuid
from datetime import date

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.person import Person
from app.schemas.dashboard import DashboardSummary, DuePersonCard


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
