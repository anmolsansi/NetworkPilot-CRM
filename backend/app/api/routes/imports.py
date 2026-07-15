import csv
import io
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.logging import get_logger
from app.models.import_job import ImportJob
from app.models.user import AppUser
from app.schemas.imports import ImportJobResponse, ImportPreviewResponse
from app.services.csv_import_service import CsvImportService
from app.services.workspace_service import require_workspace_access

router = APIRouter()
logger = get_logger(__name__)


@router.post("/people/preview", response_model=ImportPreviewResponse)
async def preview_people_import(
    workspace_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    default_initial_action_type: str = Form("invite_sent"),
    duplicate_strategy: str = Form("skip"),
    default_priority: str = Form("B"),
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_workspace_access(workspace_id, user, db)
    content = await file.read()
    service = CsvImportService(db)
    preview = await service.preview(
        workspace_id=workspace_id,
        actor_user_id=user.id,
        content=content,
        file_name=file.filename,
        default_initial_action_type=default_initial_action_type,
        duplicate_strategy=duplicate_strategy,
        default_priority=default_priority,
    )
    return preview


@router.post("/people/commit", response_model=ImportJobResponse)
async def commit_people_import(
    workspace_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    default_initial_action_type: str = Form("invite_sent"),
    duplicate_strategy: str = Form("skip"),
    default_priority: str = Form("B"),
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_workspace_access(workspace_id, user, db)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="CSV files must be 10 MB or smaller")

    # Store CSV in the database for the worker
    try:
        content_str = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")

    service = CsvImportService(db)
    rows, _provided_headers = service._parse_csv(content)
    service._validate_defaults(default_initial_action_type, default_priority)
    if duplicate_strategy not in {"skip", "update"}:
        raise HTTPException(
            status_code=422,
            detail="Only skip or update duplicate strategies are supported",
        )

    job = ImportJob(
        workspace_id=workspace_id,
        created_by_user_id=user.id,
        status="pending",
        file_content=content_str,
        file_name=file.filename,
        default_initial_action_type=default_initial_action_type,
        duplicate_strategy=duplicate_strategy,
        default_priority=default_priority,
        total_rows=len(rows),
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    return job


@router.get("/{job_id}/errors.csv")
async def download_import_errors(
    job_id: uuid.UUID,
    workspace_id: uuid.UUID,
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_workspace_access(workspace_id, user, db)
    job = await db.get(ImportJob, job_id)
    if not job or job.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Import job not found")

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["row", "errors"])
    writer.writeheader()
    for error in job.error_log or []:
        messages = error.get("errors") or [error.get("error", "Unknown error")]
        writer.writerow({"row": error.get("row", ""), "errors": "; ".join(messages)})
    filename = f"import-{job.id}-errors.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("", response_model=list[ImportJobResponse])
async def list_imports(
    workspace_id: uuid.UUID,
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_workspace_access(workspace_id, user, db)
    stmt = (
        select(ImportJob)
        .where(ImportJob.workspace_id == workspace_id)
        .order_by(ImportJob.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{job_id}", response_model=ImportJobResponse)
async def get_import(
    job_id: uuid.UUID,
    workspace_id: uuid.UUID,
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_workspace_access(workspace_id, user, db)
    job = await db.get(ImportJob, job_id)
    if not job or job.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Import job not found")
    return job


@router.post("/{job_id}/retry", response_model=ImportJobResponse)
async def retry_import(
    job_id: uuid.UUID,
    workspace_id: uuid.UUID,
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_workspace_access(workspace_id, user, db)
    job = await db.get(ImportJob, job_id)
    if not job or job.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Import job not found")

    if job.status not in {"failed", "completed"} or not job.error_log:
        raise HTTPException(
            status_code=400, detail="Only failed imports or imports with row errors can be retried"
        )
    if job.attempt_count >= 3:
        raise HTTPException(status_code=400, detail="Import retry limit reached")

    job.status = "pending"
    job.processed_rows = 0
    job.failed_rows = 0
    job.error_log = None
    job.completed_at = None
    job.started_at = None
    job.heartbeat_at = None

    await db.commit()
    await db.refresh(job)
    return job
