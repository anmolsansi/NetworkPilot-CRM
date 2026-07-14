import csv
import io
import logging
import uuid
from datetime import datetime, time, timedelta, timezone
from typing import Sequence
from zoneinfo import ZoneInfo

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.person import Person
from app.models.template import MessageTemplate
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.analytics import (
    FunnelMetrics,
    GoalMetricProgress,
    TemplatePerformance,
    WeeklyGoalProgress,
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_funnel_metrics(self, workspace_id: uuid.UUID) -> FunnelMetrics:
        """Calculate high-level funnel metrics based on current Person stages."""
        base_query = select(Person).where(
            Person.workspace_id == workspace_id,
            Person.deleted_at.is_(None),
            Person.status == "active",
        )

        total_saved_query = select(func.count()).select_from(base_query.subquery())
        contacted_query = select(func.count()).select_from(
            base_query.where(Person.stage != "saved_for_later").subquery()
        )
        replied_query = select(func.count()).select_from(
            base_query.where(Person.stage == "replied").subquery()
        )

        total_saved = (await self.db.execute(total_saved_query)).scalar() or 0
        contacted = (await self.db.execute(contacted_query)).scalar() or 0
        replied = (await self.db.execute(replied_query)).scalar() or 0

        conversion_rate = 0.0
        if contacted > 0:
            conversion_rate = round((replied / contacted) * 100, 2)

        return FunnelMetrics(
            total_saved=total_saved,
            contacted=contacted,
            replied=replied,
            conversion_rate=conversion_rate,
        )

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

        workspace = await self.db.scalar(select(Workspace).where(Workspace.id == workspace_id))
        zone = ZoneInfo(workspace.timezone)
        local_now = datetime.now(timezone.utc).astimezone(zone)
        week_start_date = local_now.date() - timedelta(days=local_now.weekday())
        local_start = datetime.combine(week_start_date, time.min, tzinfo=zone)
        local_end = local_start + timedelta(days=7)
        period_start = local_start.astimezone(timezone.utc)
        period_end = local_end.astimezone(timezone.utc)

        targets = member.weekly_goals if member else {}
        defaults = {
            "profiles_added": 25,
            "invitations_sent": 50,
            "follow_ups_sent": 25,
            "replies_received": 10,
        }
        targets = {**defaults, **(targets or {})}
        profiles_added = await self.db.scalar(
            select(func.count(Person.id)).where(
                Person.workspace_id == workspace_id,
                Person.deleted_at.is_(None),
                Person.created_at >= period_start,
                Person.created_at < period_end,
            )
        )
        activity_rows = (
            await self.db.execute(
                select(Activity.action_type, func.count(Activity.id))
                .where(
                    Activity.workspace_id == workspace_id,
                    Activity.deleted_at.is_(None),
                    Activity.created_at >= period_start,
                    Activity.created_at < period_end,
                )
                .group_by(Activity.action_type)
            )
        ).all()
        activity_counts = dict(activity_rows)
        current = {
            "profiles_added": int(profiles_added or 0),
            "invitations_sent": activity_counts.get("invite_sent", 0),
            "follow_ups_sent": activity_counts.get("follow_up_1_sent", 0),
            "replies_received": activity_counts.get("reply_received", 0),
        }
        labels = {
            "profiles_added": "Profiles added",
            "invitations_sent": "Invitations sent",
            "follow_ups_sent": "Follow-ups sent",
            "replies_received": "Replies received",
        }
        return WeeklyGoalProgress(
            timezone=workspace.timezone,
            period_start=period_start,
            period_end=period_end,
            metrics=[
                GoalMetricProgress(
                    metric=metric,
                    label=labels[metric],
                    target=targets[metric],
                    current=current[metric],
                    percentage=(
                        min(100.0, round((current[metric] / targets[metric]) * 100, 2))
                        if targets[metric] > 0
                        else 0.0
                    ),
                )
                for metric in labels
            ],
        )

    async def export_analytics_csv(self, workspace_id: uuid.UUID) -> str:
        """Export analytics as a CSV string."""
        funnel = await self.get_funnel_metrics(workspace_id)
        performance = await self.get_template_performance(workspace_id)

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Saved", funnel.total_saved])
        writer.writerow(["Contacted", funnel.contacted])
        writer.writerow(["Replied", funnel.replied])
        writer.writerow(["Overall Conversion Rate (%)", funnel.conversion_rate])
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
