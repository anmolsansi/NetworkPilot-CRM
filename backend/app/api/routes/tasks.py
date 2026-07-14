import logging
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.logging import get_logger, mask_id
from app.schemas.task import TaskCreate, TaskListResponse, TaskResponse, TaskUpdate
from app.services.task_service import TaskService
from app.services.workspace_service import require_workspace_access

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
router = APIRouter()
logger = get_logger(__name__)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    data: TaskCreate,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Create a new task."""
    logger.info(
        "tasks.create.started workspace_id=%s person_id=%s",
        mask_id(str(workspace_id)),
        mask_id(str(data.person_id)),
    )
    service = TaskService(db)
    task = await service.create(workspace_id, data)
    return task


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    workspace_id: uuid.UUID = Query(...),
    person_id: uuid.UUID | None = Query(None),
    assigned_to: uuid.UUID | None = Query(None),
    status_filter: Literal["open", "completed"] | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """List tasks in a workspace."""
    logger.info(
        "tasks.list.started workspace_id=%s person_id=%s page=%s limit=%s",
        mask_id(str(workspace_id)),
        mask_id(str(person_id)) if person_id else None,
        page,
        limit,
    )
    service = TaskService(db)
    tasks, total = await service.list(
        workspace_id=workspace_id,
        person_id=person_id,
        assigned_to=assigned_to,
        status=status_filter,
        page=page,
        limit=limit,
    )
    return TaskListResponse(
        items=[TaskResponse.model_validate(t) for t in tasks],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: uuid.UUID,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Get a task by ID."""
    service = TaskService(db)
    return await service.get(workspace_id, task_id)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: uuid.UUID,
    data: TaskUpdate,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Update a task."""
    logger.info(
        "tasks.update.started workspace_id=%s task_id=%s",
        mask_id(str(workspace_id)),
        mask_id(str(task_id)),
    )
    service = TaskService(db)
    return await service.update(workspace_id, task_id, data)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: uuid.UUID,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Delete a task."""
    logger.info(
        "tasks.delete.started workspace_id=%s task_id=%s",
        mask_id(str(workspace_id)),
        mask_id(str(task_id)),
    )
    service = TaskService(db)
    await service.delete(workspace_id, task_id)
