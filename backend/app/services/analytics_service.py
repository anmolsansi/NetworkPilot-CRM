import csv
import io
import logging
import uuid
from datetime import date, datetime, timedelta
from typing import Sequence

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.person import Person
from app.models.template import MessageTemplate
from app.models.workspace import WorkspaceMember
from app.schemas.analytics import (
    FunnelMetrics,
    FunnelStageMetrics,
    TemplatePerformance,
    WeeklyGoalProgress,
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_funnel_metrics(self, workspace_id: uuid.UUID) -> FunnelMetrics:
        """Build a cumulative funnel from durable activity events."""
        total_saved = await self.db.scalar(
            select(func.count(Person.id)).where(
                Person.workspace_id == workspace_id,
                Person.deleted_at.is_(None),
            )
        )
        event_rows = await self.db.execute(
            select(Activity.person_id, Activity.action_type)
            .join(Person, Person.id == Activity.person_id)
            .where(
                Activity.workspace_id == workspace_id,
                Activity.deleted_at.is_(None),
                Person.workspace_id == workspace_id,
                Person.deleted_at.is_(None),
            )
            .distinct()
        )
        events_by_person: dict[uuid.UUID, set[str]] = {}
        for person_id, action_type in event_rows:
            events_by_person.setdefault(person_id, set()).add(action_type)

        reached_actions = {
            "invite_sent": {
                "invite_sent",
                "accepted",
                "message_sent",
                "follow_up_1_sent",
                "reply_received",
            },
            "accepted": {
                "accepted",
                "message_sent",
                "follow_up_1_sent",
                "reply_received",
            },
            "messaged": {"message_sent", "follow_up_1_sent", "reply_received"},
            "replied": {"reply_received"},
        }
        counts = {"saved": int(total_saved or 0)}
        counts.update(
            {
                stage: sum(bool(events & actions) for events in events_by_person.values())
                for stage, actions in reached_actions.items()
            }
        )
        labels = {
            "saved": "Saved",
            "invite_sent": "Invite sent",
            "accepted": "Accepted",
            "messaged": "Messaged",
            "replied": "Replied",
        }
        ordered_stages = ["saved", "invite_sent", "accepted", "messaged", "replied"]
        stages: list[FunnelStageMetrics] = []
        for index, key in enumerate(ordered_stages):
            count = counts[key]
            previous_count = counts[ordered_stages[index - 1]] if index else count
            stages.append(
                FunnelStageMetrics(
                    key=key,
                    label=labels[key],
                    count=count,
                    conversion_from_previous=self._percentage(count, previous_count),
                    conversion_from_saved=self._percentage(count, counts["saved"]),
                )
            )
        return FunnelMetrics(stages=stages)

    @staticmethod
    def _percentage(numerator: int, denominator: int) -> float:
        if denominator == 0:
            return 0.0
        return round((numerator / denominator) * 100, 2)

    async def get_template_performance(
        self, workspace_id: uuid.UUID
    ) -> Sequence[TemplatePerformance]:
        """Calculate performance metrics for each template."""
        # A simple heuristic: Count how many times a template was used
        # and how many of those people are currently in the 'replied' stage.
        stmt = (
            select(
                MessageTemplate.id,
                MessageTemplate.name,
                func.count(Activity.id).label("sent_count"),
                func.count(
                    case(
                        (Person.stage == "replied", 1),
                        else_=None,
                    )
                ).label("reply_count"),
            )
            .join(Activity, Activity.template_id == MessageTemplate.id)
            .join(Person, Person.id == Activity.person_id)
            .where(
                MessageTemplate.workspace_id == workspace_id,
                MessageTemplate.deleted_at.is_(None),
                Activity.deleted_at.is_(None),
            )
            .group_by(MessageTemplate.id)
        )

        results = await self.db.execute(stmt)
        rows = results.all()

        performance = []
        for row in rows:
            template_id, name, sent_count, reply_count = row
            rate = 0.0
            if sent_count > 0:
                rate = round((reply_count / sent_count) * 100, 2)
            performance.append(
                TemplatePerformance(
                    template_id=template_id,
                    template_name=name,
                    sent_count=sent_count,
                    reply_count=reply_count,
                    reply_rate=rate,
                )
            )

        return performance

    async def get_weekly_goal_progress(
        self, workspace_id: uuid.UUID, user_id: uuid.UUID
    ) -> WeeklyGoalProgress:
        """Calculate progress towards the user's weekly outreach target."""
        member = (
            await self.db.execute(
                select(WorkspaceMember).where(
                    WorkspaceMember.workspace_id == workspace_id,
                    WorkspaceMember.user_id == user_id,
                )
            )
        ).scalar_one_or_none()

        target = member.weekly_outreach_target if member else 50

        # Calculate start of the current week (Monday)
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        start_datetime = datetime.combine(start_of_week, datetime.min.time())

        # Count activities (e.g., messages sent) this week by this user
        count_stmt = select(func.count(Activity.id)).where(
            Activity.actor_id == user_id,
            Activity.created_at >= start_datetime,
            Activity.deleted_at.is_(None),
            Activity.activity_type.in_(["message_sent", "connection_sent", "email_sent"]),
        )
        current = (await self.db.execute(count_stmt)).scalar() or 0

        percentage = 0.0
        if target > 0:
            percentage = min(100.0, round((current / target) * 100, 2))

        return WeeklyGoalProgress(
            target=target,
            current=current,
            percentage=percentage,
        )

    async def export_analytics_csv(self, workspace_id: uuid.UUID) -> str:
        """Export analytics as a CSV string."""
        funnel = await self.get_funnel_metrics(workspace_id)
        performance = await self.get_template_performance(workspace_id)

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["Metric", "Value"])
        writer.writerow(["Funnel Stage", "Count", "From Previous (%)", "From Saved (%)"])
        for stage in funnel.stages:
            writer.writerow(
                [
                    stage.label,
                    stage.count,
                    stage.conversion_from_previous,
                    stage.conversion_from_saved,
                ]
            )
        writer.writerow([])

        writer.writerow(["Template Performance"])
        writer.writerow(
            ["Template ID", "Template Name", "Sent Count", "Reply Count", "Reply Rate (%)"]
        )
        for p in performance:
            writer.writerow(
                [str(p.template_id), p.template_name, p.sent_count, p.reply_count, p.reply_rate]
            )

        return output.getvalue()
