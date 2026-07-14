import asyncio
import logging
import sys
from datetime import datetime, timedelta, timezone
from html import escape
from zoneinfo import ZoneInfo

import resend
from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.background_job import BackgroundJob
from app.models.import_job import ImportJob
from app.models.notification import Notification
from app.models.person import Person
from app.models.workspace import Workspace
from app.schemas.imports import ImportCommitRequest, ImportCommitRow
from app.services.csv_import_service import CsvImportService

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("worker")

engine = create_async_engine(str(settings.DATABASE_URL), pool_pre_ping=True)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

IMPORT_BATCH_SIZE = 40


async def process_job(db: AsyncSession, job: ImportJob):
    """Validate and import a queued CSV in durable 40-row batches."""
    logger.info("import_job.started job_id=%s attempt=%s", job.id, job.attempt_count)
    service = CsvImportService(db)
    rows, provided_headers = service._parse_csv(job.file_content.encode("utf-8"))
    job.total_rows = len(rows)
    job.processed_rows = 0
    job.failed_rows = 0
    job.error_log = []
    await db.commit()

    errors: list[dict] = []
    total_chunks = max(1, (len(rows) + IMPORT_BATCH_SIZE - 1) // IMPORT_BATCH_SIZE)
    for chunk_index, offset in enumerate(range(0, len(rows), IMPORT_BATCH_SIZE)):
        chunk = rows[offset : offset + IMPORT_BATCH_SIZE]
        preview_rows = await service._validate_rows(
            workspace_id=job.workspace_id,
            rows=chunk,
            duplicate_strategy=job.duplicate_strategy,
            default_initial_action_type=job.default_initial_action_type,
            default_priority=job.default_priority,
        )
        committable_rows = [
            row for row in preview_rows if row.status in {"valid", "update"}
        ]
        for row_error in preview_rows:
            if row_error.status in {"valid", "update"}:
                continue
            payload = row_error.model_dump(mode="json")
            payload["row"] = offset + payload["row_number"]
            if row_error.status == "duplicate" and not payload["errors"]:
                payload["errors"] = ["Duplicate LinkedIn profile URL"]
            errors.append(payload)

        if committable_rows:
            request = ImportCommitRequest(
                workspace_id=job.workspace_id,
                default_initial_action_type=job.default_initial_action_type,
                duplicate_strategy=job.duplicate_strategy,
                default_priority=job.default_priority,
                provided_headers=provided_headers,
                rows=[ImportCommitRow(**row.model_dump()) for row in committable_rows],
                chunk_index=chunk_index,
                total_chunks=total_chunks,
            )
            result = await service.commit(job.created_by_user_id, request)
            for row_error in result["errors"]:
                payload = row_error.model_dump(mode="json")
                payload["row"] = offset + payload["row_number"]
                errors.append(payload)
        job.processed_rows += len(chunk)
        job.failed_rows = len(errors)
        job.error_log = errors or None
        job.heartbeat_at = datetime.utcnow()
        await db.commit()

    job.status = "completed"
    job.completed_at = datetime.utcnow()
    await db.commit()
    logger.info(
        "import_job.completed job_id=%s processed=%s failed=%s",
        job.id,
        job.processed_rows,
        job.failed_rows,
    )


async def process_background_job(db: AsyncSession, job: BackgroundJob):
    """Process a generic background job."""
    logger.info("background_job.started job_id=%s type=%s", job.id, job.job_type)

    if job.job_type == "daily_digest":
        try:
            workspace_id = job.workspace_id
            ws = (
                await db.execute(select(Workspace).where(Workspace.id == workspace_id))
            ).scalar_one()
            now_utc = datetime.now(timezone.utc)
            local_now = now_utc.astimezone(ZoneInfo(ws.timezone))

            if (
                ws.quiet_hours_start
                and ws.quiet_hours_end
                and _in_quiet_hours(local_now.time(), ws.quiet_hours_start, ws.quiet_hours_end)
            ):
                job.status = "pending"
                job.run_at = _next_local_time(local_now, ws.quiet_hours_end).astimezone(
                    timezone.utc
                )
                await db.commit()
                return

            today = local_now.date()
            stmt = select(Person).where(
                Person.workspace_id == workspace_id,
                Person.deleted_at.is_(None),
                Person.next_action_date.is_not(None),
                Person.next_action_date <= today,
            )
            result = await db.execute(stmt)
            people = result.scalars().all()

            due_people = list(people)
            if due_people:
                overdue_count = sum(person.next_action_date < today for person in due_people)
                db.add(
                    Notification(
                        workspace_id=workspace_id,
                        user_id=ws.owner_id,
                        notification_type="overdue_alert"
                        if overdue_count and ws.overdue_alerts_enabled
                        else "daily_digest",
                        title=(
                            f"{len(due_people)} follow-up{'s' if len(due_people) != 1 else ''} due"
                        ),
                        body=(
                            f"{overdue_count} overdue and "
                            f"{len(due_people) - overdue_count} due today."
                        ),
                    )
                )

                if (
                    ws.email_reminders_enabled
                    and ws.daily_digest_enabled
                    and settings.RESEND_API_KEY
                    and ws.owner.email
                ):
                    resend.api_key = settings.RESEND_API_KEY
                    html_content = f"<h2>Daily Digest for {escape(ws.name)}</h2><ul>"
                    for p in due_people:
                        html_content += (
                            f"<li>{escape(p.name)} - Due: {p.next_action_date} - "
                            f"{escape(p.next_action_type or 'Follow up')}</li>"
                        )
                    html_content += "</ul>"
                    try:
                        await asyncio.to_thread(
                            resend.Emails.send,
                            {
                                "from": settings.RESEND_FROM_EMAIL,
                                "to": ws.owner.email,
                                "subject": (
                                    f"NetworkPilot Daily Digest: {len(due_people)} tasks due"
                                ),
                                "html": html_content,
                            },
                        )
                    except Exception:
                        logger.exception("background_job.email_failed job_id=%s", job.id)
                        job.error_log = (
                            "Digest email delivery failed; the in-app notification was still "
                            "created."
                        )

            if ws.daily_digest_enabled:
                next_run = _next_local_time(local_now, ws.daily_reminder_time).astimezone(
                    timezone.utc
                )
                db.add(
                    BackgroundJob(
                        workspace_id=workspace_id,
                        job_type="daily_digest",
                        status="pending",
                        run_at=next_run,
                    )
                )
            job.status = "completed"
        except Exception as e:
            job.status = "failed"
            job.error_log = str(e)
    else:
        job.status = "failed"
        job.error_log = "Unknown job_type"

    job.completed_at = datetime.utcnow()
    await db.commit()


def _in_quiet_hours(current, start, end) -> bool:
    return start <= current < end if start < end else current >= start or current < end


def _next_local_time(local_now: datetime, target_time) -> datetime:
    candidate = datetime.combine(local_now.date(), target_time, tzinfo=local_now.tzinfo)
    if candidate <= local_now:
        candidate += timedelta(days=1)
    return candidate


async def poll_import_jobs():
    logger.info("Starting ImportJob poller...")
    while True:
        async with AsyncSessionLocal() as db:
            stale_before = datetime.utcnow() - timedelta(minutes=5)
            await db.execute(
                update(ImportJob)
                .where(
                    ImportJob.status == "processing",
                    or_(
                        ImportJob.heartbeat_at < stale_before,
                        and_(
                            ImportJob.heartbeat_at.is_(None),
                            ImportJob.created_at < stale_before,
                        ),
                    ),
                    ImportJob.attempt_count < 3,
                )
                .values(status="pending")
            )
            await db.commit()
            stmt = (
                select(ImportJob)
                .where(ImportJob.status == "pending")
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            result = await db.execute(stmt)
            job = result.scalar_one_or_none()
            if job:
                job.status = "processing"
                job.attempt_count += 1
                job.started_at = datetime.utcnow()
                job.heartbeat_at = job.started_at
                await db.commit()
                try:
                    await process_job(db, job)
                except Exception:
                    logger.exception("import_job.fatal job_id=%s", job.id)
                    async with AsyncSessionLocal() as db_fallback:
                        job_fallback = await db_fallback.get(ImportJob, job.id)
                        if job_fallback:
                            job_fallback.status = "failed"
                            job_fallback.error_log = [
                                {"error": "The import worker could not process this file."}
                            ]
                            job_fallback.completed_at = datetime.utcnow()
                            await db_fallback.commit()
            else:
                await asyncio.sleep(2)


async def poll_background_jobs():
    logger.info("Starting BackgroundJob poller...")
    while True:
        async with AsyncSessionLocal() as db:
            stmt = (
                select(BackgroundJob)
                .where(BackgroundJob.status == "pending", BackgroundJob.run_at <= datetime.utcnow())
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            result = await db.execute(stmt)
            job = result.scalar_one_or_none()
            if job:
                job.status = "processing"
                await db.commit()
                try:
                    await process_background_job(db, job)
                except Exception as e:
                    logger.exception(f"Fatal error processing BackgroundJob {job.id}")
                    async with AsyncSessionLocal() as db_fallback:
                        job_fallback = await db_fallback.get(BackgroundJob, job.id)
                        if job_fallback:
                            job_fallback.status = "failed"
                            job_fallback.error_log = f"Fatal worker error: {str(e)}"
                            job_fallback.completed_at = datetime.utcnow()
                            await db_fallback.commit()
            else:
                await asyncio.sleep(2)


async def run_worker():
    await asyncio.gather(poll_import_jobs(), poll_background_jobs())


if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker stopped.")
