import csv
import io
import logging
import uuid
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.person import Person
from app.models.template import MessageTemplate
from app.models.workspace import WorkspaceMember
from app.schemas.analytics import FunnelMetrics, PerformanceBreakdown, WeeklyGoalProgress
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
        self,
        workspace_id: uuid.UUID,
        *,
        group_by: str = "template",
        date_from: date | None = None,
        date_to: date | None = None,
        attribution_days: int = 30,
    ) -> Sequence[PerformanceBreakdown]:
        """Attribute each reply to the latest eligible send for the same person."""
        send_query = (
            select(Activity, Person, MessageTemplate)
            .join(Person, Person.id == Activity.person_id)
            .outerjoin(MessageTemplate, MessageTemplate.id == Activity.template_id)
            .where(
                Activity.workspace_id == workspace_id,
                Activity.action_type.in_(["message_sent", "follow_up_1_sent"]),
                Activity.deleted_at.is_(None),
                Person.workspace_id == workspace_id,
                Person.deleted_at.is_(None),
            )
            .order_by(Activity.created_at)
        )
        if date_from:
            send_query = send_query.where(
                Activity.created_at >= datetime.combine(date_from, time.min, tzinfo=timezone.utc)
            )
        if date_to:
            send_query = send_query.where(
                Activity.created_at <= datetime.combine(date_to, time.max, tzinfo=timezone.utc)
            )
        send_rows = (await self.db.execute(send_query)).all()
        if not send_rows:
            return []

        sends_by_person: dict[uuid.UUID, list[Activity]] = defaultdict(list)
        send_context: dict[uuid.UUID, tuple[Activity, Person, MessageTemplate | None]] = {}
        for activity, person, template in send_rows:
            sends_by_person[activity.person_id].append(activity)
            send_context[activity.id] = (activity, person, template)

        first_sent = min(self._as_utc(row[0].created_at) for row in send_rows)
        last_sent = max(self._as_utc(row[0].created_at) for row in send_rows)
        replies = (
            await self.db.scalars(
                select(Activity)
                .where(
                    Activity.workspace_id == workspace_id,
                    Activity.person_id.in_(sends_by_person),
                    Activity.action_type == "reply_received",
                    Activity.deleted_at.is_(None),
                    Activity.created_at >= first_sent,
                    Activity.created_at <= last_sent + timedelta(days=attribution_days),
                )
                .order_by(Activity.created_at)
            )
        ).all()
        credited_send_ids: set[uuid.UUID] = set()
        for reply in replies:
            reply_at = self._as_utc(reply.created_at)
            candidates = [
                send
                for send in sends_by_person[reply.person_id]
                if self._as_utc(send.created_at) <= reply_at
                and reply_at - self._as_utc(send.created_at) <= timedelta(days=attribution_days)
            ]
            if candidates:
                latest_send = max(candidates, key=lambda item: self._as_utc(item.created_at))
                credited_send_ids.add(latest_send.id)

        grouped: dict[tuple[str, str], dict[str, int]] = defaultdict(
            lambda: {"sent": 0, "replied": 0}
        )
        for send, person, template in send_rows:
            key, label = self._performance_dimension(group_by, send, person, template)
            grouped[(key, label)]["sent"] += 1
            if send.id in credited_send_ids:
                grouped[(key, label)]["replied"] += 1

        return [
            PerformanceBreakdown(
                dimension=group_by,
                dimension_key=key,
                dimension_label=label,
                sent_count=counts["sent"],
                reply_count=counts["replied"],
                reply_rate=round((counts["replied"] / counts["sent"]) * 100, 2),
                date_from=date_from,
                date_to=date_to,
            )
            for (key, label), counts in sorted(grouped.items(), key=lambda item: item[0][1])
        ]

    @staticmethod
    def _performance_dimension(
        group_by: str,
        activity: Activity,
        person: Person,
        template: MessageTemplate | None,
    ) -> tuple[str, str]:
        if group_by == "template":
            return (
                str(template.id) if template else "untemplated",
                template.name if template else "No template",
            )
        if group_by == "stage":
            value = activity.previous_stage or "unknown"
        elif group_by == "company":
            value = person.company or "Unknown company"
        elif group_by == "position":
            value = person.role or "Unknown position"
        else:
            week_start = AnalyticsService._as_utc(activity.created_at).date()
            week_start -= timedelta(days=week_start.weekday())
            value = week_start.isoformat()
        return value, value.replace("_", " ").title() if group_by == "stage" else value

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

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

        writer.writerow(["Follow-up Performance"])
        writer.writerow(["Group Key", "Group Label", "Sent Count", "Reply Count", "Reply Rate (%)"])
        for p in performance:
            writer.writerow(
                [p.dimension_key, p.dimension_label, p.sent_count, p.reply_count, p.reply_rate]
            )

        return output.getvalue()
