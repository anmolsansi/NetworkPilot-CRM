import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import AppUser
from app.schemas.people import (
    ArchiveRequest,
    PersonCreate,
    PersonListResponse,
    PersonResponse,
    PersonUpdate,
    SnoozeRequest,
)
from app.services.people_service import PeopleService
from app.services.workspace_service import require_workspace_access

router = APIRouter()


@router.get("", response_model=PersonListResponse)
async def list_people(
    workspace_id: uuid.UUID = Query(...),
    stage: str | None = Query(None),
    priority: str | None = Query(None),
    status: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """List people in workspace with filters."""
    service = PeopleService(db)
    people, total = await service.list(
        workspace_id=workspace_id,
        stage=stage,
        priority=priority,
        status=status,
        search=search,
        page=page,
        limit=limit,
    )
    return PersonListResponse(
        items=[PersonResponse.model_validate(p) for p in people],
        total=total,
        page=page,
        limit=limit,
    )


@router.post("", response_model=PersonResponse, status_code=201)
async def create_person(
    data: PersonCreate,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Create a new person."""
    service = PeopleService(db)
    person = await service.create(workspace_id, data)
    return person


@router.get("/{person_id}", response_model=PersonResponse)
async def get_person(
    person_id: uuid.UUID,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Get a person by ID."""
    service = PeopleService(db)
    person = await service.get(workspace_id, person_id)
    return person


@router.patch("/{person_id}", response_model=PersonResponse)
async def update_person(
    person_id: uuid.UUID,
    data: PersonUpdate,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Update a person."""
    service = PeopleService(db)
    person = await service.update(workspace_id, person_id, data)
    return person


@router.delete("/{person_id}", status_code=204)
async def delete_person(
    person_id: uuid.UUID,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a person."""
    service = PeopleService(db)
    await service.soft_delete(workspace_id, person_id)


@router.post("/{person_id}/snooze", response_model=PersonResponse)
async def snooze_person(
    person_id: uuid.UUID,
    data: SnoozeRequest,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Snooze a person until a date."""
    service = PeopleService(db)
    person = await service.snooze(workspace_id, person_id, data.until_date)
    return person


@router.post("/{person_id}/archive", response_model=PersonResponse)
async def archive_person(
    person_id: uuid.UUID,
    data: ArchiveRequest,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Archive a person."""
    service = PeopleService(db)
    person = await service.archive(workspace_id, person_id)
    return person
