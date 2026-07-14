import logging
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.person import Person
from app.core.errors import NotFoundError

_module_logger = logging.getLogger(__name__)


class RelationshipService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def recalculate_freshness(self, workspace_id: uuid.UUID, person_id: uuid.UUID) -> Person:
        """
        Calculate freshness (0-100) based on recent activities.
        Decay algorithm: 
        - If engaged in the last 7 days: 100
        - If engaged in the last 14 days: 80
        - If engaged in the last 30 days: 50
        - If engaged in the last 60 days: 20
        - Otherwise: 0
        """
        result = await self.db.execute(
            select(Person).where(
                Person.id == person_id,
                Person.workspace_id == workspace_id,
                Person.deleted_at.is_(None)
            )
        )
        person = result.scalar_one_or_none()
        if not person:
            raise NotFoundError("Person", str(person_id))

        # Find the most recent interaction activity
        activity_result = await self.db.execute(
            select(Activity).where(
                Activity.person_id == person_id,
                Activity.workspace_id == workspace_id,
                Activity.deleted_at.is_(None)
            ).order_by(Activity.created_at.desc()).limit(1)
        )
        latest_activity = activity_result.scalar_one_or_none()

        if latest_activity:
            person.last_engaged_at = latest_activity.created_at
            
            activity_date = latest_activity.created_at
            if activity_date.tzinfo is None:
                activity_date = activity_date.replace(tzinfo=timezone.utc)
            
            days_ago = (datetime.now(timezone.utc) - activity_date).days
            
            if days_ago <= 7:
                person.calculated_freshness = 100
            elif days_ago <= 14:
                person.calculated_freshness = 80
            elif days_ago <= 30:
                person.calculated_freshness = 50
            elif days_ago <= 60:
                person.calculated_freshness = 20
            else:
                person.calculated_freshness = 0
        else:
            person.calculated_freshness = 0

        await self.db.flush()
        _module_logger.info("relationship_service.recalculated person_id=%s freshness=%s", person_id, person.calculated_freshness)
        return person
