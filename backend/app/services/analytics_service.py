import csv
import io
import logging
import uuid
from datetime import date, datetime, timedelta
from typing import Sequence

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.person import Person
from app.models.template import MessageTemplate
from app.models.workspace import WorkspaceMember
from app.schemas.analytics import FunnelMetrics, TemplatePerformance, WeeklyGoalProgress

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
