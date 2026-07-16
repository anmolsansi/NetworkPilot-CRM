import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.activity import Activity
from app.models.person import Person

_module_logger = logging.getLogger(__name__)


class RelationshipService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def recalculate_freshness(
        self,
        workspace_id: uuid.UUID,
        person_id: uuid.UUID,
        *,
        now: datetime | None = None,
    ) -> Person:
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
                Person.deleted_at.is_(None),
            )
        )
        person = result.scalar_one_or_none()
        if not person:
            raise NotFoundError("Person", str(person_id))

        now = self._as_utc(now or datetime.now(timezone.utc))

        # Find the most recent interaction activity and interaction volume.
        activity_result = await self.db.execute(
            select(Activity)
            .where(
                Activity.person_id == person_id,
                Activity.workspace_id == workspace_id,
                Activity.deleted_at.is_(None),
            )
            .order_by(Activity.created_at.desc())
            .limit(1)
        )
        latest_activity = activity_result.scalar_one_or_none()
        activity_count = await self.db.scalar(
            select(func.count(Activity.id)).where(
                Activity.person_id == person_id,
                Activity.workspace_id == workspace_id,
                Activity.deleted_at.is_(None),
            )
        )

        if latest_activity:
            activity_date = self._as_utc(latest_activity.created_at)
            person.last_engaged_at = activity_date
            person.calculated_freshness = self.freshness_for(activity_date, now)
        else:
            person.calculated_freshness = 0
            person.last_engaged_at = None

        # Engagement rewards interaction volume while freshness captures recency.
        person.engagement_score = min(
            100,
            int(person.calculated_freshness * 0.6) + min(int(activity_count or 0), 10) * 4,
        )
        effective_score = (
            person.manual_warmth * 20
            if person.manual_warmth is not None
            else round((person.calculated_freshness + person.engagement_score) / 2)
        )
        person.relationship_health = self.health_for(effective_score)

        await self.db.flush()
        _module_logger.info(
            "relationship_service.recalculated person_id=%s freshness=%s",
            person_id,
            person.calculated_freshness,
        )
        return person

    async def refresh_workspace(
        self, workspace_id: uuid.UUID, *, now: datetime | None = None
    ) -> int:
        """Backfill time-dependent relationship indicators for active people."""
        person_ids = (
            await self.db.scalars(
                select(Person.id).where(
                    Person.workspace_id == workspace_id,
                    Person.deleted_at.is_(None),
                )
            )
        ).all()
        for person_id in person_ids:
            await self.recalculate_freshness(workspace_id, person_id, now=now)
        return len(person_ids)

    @staticmethod
    def freshness_for(activity_date: datetime, now: datetime) -> int:
        days_ago = max(0, (now - RelationshipService._as_utc(activity_date)).days)
        if days_ago <= 7:
            return 100
        if days_ago <= 14:
            return 80
        if days_ago <= 30:
            return 50
        if days_ago <= 60:
            return 20
        return 0

    @staticmethod
    def health_for(score: int) -> str:
        if score >= 80:
            return "strong"
        if score >= 60:
            return "healthy"
        if score >= 30:
            return "needs_attention"
        return "cold"

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
