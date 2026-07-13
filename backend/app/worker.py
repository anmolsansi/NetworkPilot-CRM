import asyncio
import csv
import io
import logging
import uuid
import sys
from datetime import datetime

from sqlalchemy import select, update, exc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.core.config import settings
from app.models.import_job import ImportJob
from app.models.person import Person
from app.models.workspace import Workspace
from app.models.background_job import BackgroundJob
import resend

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("worker")

engine = create_async_engine(str(settings.DATABASE_URL), pool_pre_ping=True)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def process_job(db: AsyncSession, job: ImportJob):
    """Parse CSV and insert/update people records."""
    logger.info(f"Processing job {job.id}")
    
    file_content = job.file_content
    f = io.StringIO(file_content)
    reader = csv.DictReader(f)
    
    if not reader.fieldnames:
        job.status = "failed"
        job.error_log = [{"error": "Empty or invalid CSV"}]
        return

    # To count total rows if we don't have it (or just count as we go)
    rows = list(reader)
    job.total_rows = len(rows)
    job.processed_rows = 0
    job.error_log = []
    
    # We must commit the initial "processing" status and row count
    await db.commit()
    
    # Simple mapping
    # Assuming CSV has 'first_name', 'last_name', 'linkedin_url' at minimum
    error_log = []
    for i, row in enumerate(rows):
        try:
            linkedin_url = row.get("linkedin_url")
            if not linkedin_url:
                error_log.append({"row": i + 2, "error": "Missing linkedin_url"})
                continue
                
            # Upsert logic (simplistic: insert if not exists)
            stmt = select(Person).where(
                Person.workspace_id == job.workspace_id,
                Person.linkedin_url == linkedin_url
            )
            result = await db.execute(stmt)
            person = result.scalar_one_or_none()
            
            if not person:
                person = Person(
                    workspace_id=job.workspace_id,
                    linkedin_url=linkedin_url,
                    first_name=row.get("first_name", ""),
                    last_name=row.get("last_name", ""),
                    company=row.get("company", ""),
                    role=row.get("role", ""),
                    email=row.get("email", ""),
                )
                db.add(person)
            else:
                # Update empty fields
                if not person.first_name and row.get("first_name"):
                    person.first_name = row.get("first_name")
                if not person.last_name and row.get("last_name"):
                    person.last_name = row.get("last_name")
                if not person.company and row.get("company"):
                    person.company = row.get("company")

        except Exception as e:
            error_log.append({"row": i + 2, "error": str(e)})

        job.processed_rows += 1
        
        # Periodically commit to update progress and save memory
        if job.processed_rows % 50 == 0:
            await db.commit()

    job.status = "completed"
    if error_log:
        job.error_log = error_log
    job.completed_at = datetime.utcnow()
    await db.commit()
    logger.info(f"Completed job {job.id} with {len(error_log)} errors.")

async def process_background_job(db: AsyncSession, job: BackgroundJob):
    """Process a generic background job."""
    logger.info(f"Processing BackgroundJob {job.id} of type {job.job_type}")
    
    if job.job_type == "daily_digest":
        try:
            # 1. Fetch due tasks for the workspace
            workspace_id = job.workspace_id
            
            # Simple check: due tasks could be next_action_date <= today
            # or any priority A folks. We'll just list people with next_action_date
            today = datetime.utcnow().date()
            stmt = select(Person).where(
                Person.workspace_id == workspace_id,
                Person.next_action_date != None
            )
            result = await db.execute(stmt)
            people = result.scalars().all()
            
            due_people = []
            for p in people:
                try:
                    # next_action_date is string 'YYYY-MM-DD'
                    p_date = datetime.strptime(p.next_action_date, "%Y-%m-%d").date()
                    if p_date <= today:
                        due_people.append(p)
                except:
                    pass
            
            # Send email if there are due tasks or if we just want to send a digest
            if due_people:
                resend.api_key = settings.RESEND_API_KEY
                
                # We need the workspace owner's email
                stmt_ws = select(Workspace).where(Workspace.id == workspace_id)
                ws = (await db.execute(stmt_ws)).scalar_one()
                
                if not ws.owner.email:
                    logger.warning(f"Workspace {workspace_id} owner has no email")
                else:
                    html_content = f"<h2>Daily Digest for {ws.name}</h2><ul>"
                    for p in due_people:
                        html_content += f"<li>{p.name} - Due: {p.next_action_date} - {p.next_action_type}</li>"
                    html_content += "</ul>"
                    
                    try:
                        r = resend.Emails.send({
                            "from": settings.RESEND_FROM_EMAIL,
                            "to": ws.owner.email,
                            "subject": f"NetworkPilot Daily Digest: {len(due_people)} tasks due",
                            "html": html_content
                        })
                        logger.info(f"Sent digest email for workspace {workspace_id}, response: {r}")
                    except Exception as e:
                        logger.error(f"Failed to send resend email: {e}")
                        job.error_log = str(e)
                        
            # Schedule next day's job
            now = datetime.utcnow()
            # Simplistic scheduling: tomorrow at same time, ignoring workspace timezone for now to avoid pytz dependency, 
            # but using workspace.daily_reminder_time if possible
            # ws.daily_reminder_time is a datetime.time object
            from datetime import timedelta
            next_run_date = now.date() + timedelta(days=1)
            next_run = datetime.combine(next_run_date, ws.daily_reminder_time)
            
            new_job = BackgroundJob(
                workspace_id=workspace_id,
                job_type="daily_digest",
                status="pending",
                run_at=next_run
            )
            db.add(new_job)
            
            job.status = "completed"
        except Exception as e:
            job.status = "failed"
            job.error_log = str(e)
    else:
        job.status = "failed"
        job.error_log = "Unknown job_type"
        
    job.completed_at = datetime.utcnow()
    await db.commit()

async def poll_import_jobs():
    logger.info("Starting ImportJob poller...")
    while True:
        async with AsyncSessionLocal() as db:
            stmt = select(ImportJob).where(ImportJob.status == "pending").with_for_update(skip_locked=True).limit(1)
            result = await db.execute(stmt)
            job = result.scalar_one_or_none()
            if job:
                job.status = "processing"
                await db.commit()
                try:
                    await process_job(db, job)
                except Exception as e:
                    logger.exception(f"Fatal error processing ImportJob {job.id}")
                    async with AsyncSessionLocal() as db_fallback:
                        job_fallback = await db_fallback.get(ImportJob, job.id)
                        if job_fallback:
                            job_fallback.status = "failed"
                            job_fallback.error_log = [{"error": f"Fatal worker error: {str(e)}"}]
                            job_fallback.completed_at = datetime.utcnow()
                            await db_fallback.commit()
            else:
                await asyncio.sleep(2)

async def poll_background_jobs():
    logger.info("Starting BackgroundJob poller...")
    while True:
        async with AsyncSessionLocal() as db:
            stmt = select(BackgroundJob).where(
                BackgroundJob.status == "pending",
                BackgroundJob.run_at <= datetime.utcnow()
            ).with_for_update(skip_locked=True).limit(1)
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
    await asyncio.gather(
        poll_import_jobs(),
        poll_background_jobs()
    )

if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker stopped.")
