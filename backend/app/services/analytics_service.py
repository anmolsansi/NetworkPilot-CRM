import csv
import io
import logging
import uuid
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from typing import Sequence
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.person import Person
from app.models.template import MessageTemplate
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.analytics import (
    FunnelMetrics,
    FunnelStageMetrics,
    GoalMetricProgress,
    PerformanceBreakdown,
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

    async def get_report_rows(
        self, workspace_id: uuid.UUID, date_from: date | None, date_to: date | None
    ) -> list[tuple[str, int]]:
        person_query = select(func.count(Person.id)).where(
            Person.workspace_id == workspace_id, Person.deleted_at.is_(None)
        )
        activity_query = select(Activity.action_type, func.count(Activity.id)).where(
            Activity.workspace_id == workspace_id, Activity.deleted_at.is_(None)
        )
        if date_from:
            start = datetime.combine(date_from, datetime.min.time())
            person_query = person_query.where(Person.created_at >= start)
            activity_query = activity_query.where(Activity.created_at >= start)
        if date_to:
            end = datetime.combine(date_to + timedelta(days=1), datetime.min.time())
            person_query = person_query.where(Person.created_at < end)
            activity_query = activity_query.where(Activity.created_at < end)
        activity_counts = dict(
            (await self.db.execute(activity_query.group_by(Activity.action_type))).all()
        )
        return [
            ("Profiles saved", int(await self.db.scalar(person_query) or 0)),
            ("Invitations sent", activity_counts.get("invite_sent", 0)),
            ("Accepted", activity_counts.get("accepted", 0)),
            (
                "Messages sent",
                activity_counts.get("message_sent", 0) + activity_counts.get("follow_up_1_sent", 0),
            ),
            ("Replies received", activity_counts.get("reply_received", 0)),
        ]

    async def export_analytics_csv(
        self, workspace_id: uuid.UUID, date_from: date | None = None, date_to: date | None = None
    ) -> str:
        """Export analytics as a CSV string."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["NetworkPilot Analytics Report"])
        writer.writerow(["Date from", date_from.isoformat() if date_from else "All time"])
        writer.writerow(["Date to", date_to.isoformat() if date_to else "All time"])
        writer.writerow([])
        writer.writerow(["Metric", "Count"])
        writer.writerows(await self.get_report_rows(workspace_id, date_from, date_to))
        return output.getvalue()

    async def export_analytics_pdf(
        self, workspace_id: uuid.UUID, date_from: date | None = None, date_to: date | None = None
    ) -> bytes:
        output = io.BytesIO()
        document = SimpleDocTemplate(
            output,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
        )
        styles = getSampleStyleSheet()
        period_start = date_from.isoformat() if date_from else "All time"
        period_end = date_to.isoformat() if date_to else "present"
        period = f"{period_start} to {period_end}"
        table = Table(
            [["Metric", "Count"], *await self.get_report_rows(workspace_id, date_from, date_to)],
            colWidths=[125 * mm, 30 * mm],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#f8fafc")],
                    ),
                    ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        document.build(
            [
                Paragraph("NetworkPilot Analytics Report", styles["Title"]),
                Spacer(1, 4 * mm),
                Paragraph(f"Reporting period: {period}", styles["BodyText"]),
                Spacer(1, 7 * mm),
                table,
            ]
        )
        return output.getvalue()
