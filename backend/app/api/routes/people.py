import logging
import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.logging import get_logger, mask_id
from app.models.user import AppUser
from app.schemas.people import (
    ArchiveRequest,
    BulkPeopleActionRequest,
    BulkPeopleActionResponse,
    PersonCreate,
    PersonListResponse,
    PersonResponse,
    PersonUpdate,
    SnoozeRequest,
)
from app.services.bulk_people_service import BulkPeopleService
from app.services.people_service import PeopleService
from app.services.workspace_service import require_workspace_access

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=PersonListResponse)
async def list_people(
    workspace_id: uuid.UUID = Query(...),
    stage: str | None = Query(None),
    priority: str | None = Query(None),
    status: str | None = Query(None),
    search: str | None = Query(None),
    company: str | None = Query(None),
    role: str | None = Query(None),
    email: str | None = Query(None),
    location: str | None = Query(None),
    premium: bool | None = Query(None),
    processed_from: datetime | None = Query(None),
    processed_to: datetime | None = Query(None),
    favorite: bool | None = Query(None),
    favorite_notes: str | None = Query(None),
    sort_by: Literal[
        "linkedin_url", "first_name", "last_name", "company", "role", "email",
        "phone_number", "premium", "location", "company_website", "processed_at",
        "processed_at_millis", "invite_accepted_at", "invite_accepted_at_millis",
        "created_at", "is_favorite", "favorite_notes",
    ] = Query("created_at"),
    sort_order: Literal["asc", "desc"] = Query("desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """List people in workspace with filters."""
    logger.info(
        "people.list.started workspace_id=%s page=%s limit=%s stage=%s priority=%s status=%s",
        mask_id(str(workspace_id)),
        page,
        limit,
        stage,
        priority,
        status,
    )
    service = PeopleService(db)
    people, total = await service.list(
        workspace_id=workspace_id,
        stage=stage,
        priority=priority,
        status=status,
        search=search,
        company=company,
        role=role,
        email=email,
        location=location,
        premium=premium,
        processed_from=processed_from,
        processed_to=processed_to,
        favorite=favorite,
        favorite_notes=favorite_notes,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        limit=limit,
    )
    logger.info(
        "people.list.completed workspace_id=%s count=%s total=%s",
        mask_id(str(workspace_id)),
        len(people),
        total,
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
    logger.info(
        "people.create.started workspace_id=%s priority=%s url_present=%s",
        mask_id(str(workspace_id)),
        data.priority,
        bool(data.linkedin_url),
    )
    service = PeopleService(db)
    person = await service.create(workspace_id, data)
    logger.info(
        "people.create.completed workspace_id=%s person_id=%s stage=%s",
        mask_id(str(workspace_id)),
        mask_id(str(person.id)),
        person.stage,
    )
    return person


@router.post("/bulk-actions", response_model=BulkPeopleActionResponse)
async def bulk_people_action(
    data: BulkPeopleActionRequest,
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Apply one atomic action to an explicit workspace-scoped selection."""
    logger.info(
        "people.bulk_action.started workspace_id=%s user_id=%s action=%s count=%s",
        mask_id(str(data.workspace_id)),
        mask_id(str(user.id)),
        data.action,
        len(data.person_ids),
    )
    await require_workspace_access(data.workspace_id, user, db)
    service = BulkPeopleService(db)
    people = await service.apply(data.workspace_id, user.id, data)
    logger.info(
        "people.bulk_action.completed workspace_id=%s action=%s count=%s",
        mask_id(str(data.workspace_id)),
        data.action,
        len(people),
    )
    return BulkPeopleActionResponse(
        updated_count=len(people),
        items=[PersonResponse.model_validate(person) for person in people],
    )


@router.get("/{person_id}", response_model=PersonResponse)
async def get_person(
    person_id: uuid.UUID,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Get a person by ID."""
    logger.info(
        "people.get.started workspace_id=%s person_id=%s",
        mask_id(str(workspace_id)),
        mask_id(str(person_id)),
    )
    service = PeopleService(db)
    person = await service.get(workspace_id, person_id)
    logger.info(
        "people.get.completed workspace_id=%s person_id=%s stage=%s",
        mask_id(str(workspace_id)),
        mask_id(str(person.id)),
        person.stage,
    )
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
    logger.info(
        "people.update.started workspace_id=%s person_id=%s fields=%s",
        mask_id(str(workspace_id)),
        mask_id(str(person_id)),
        sorted(data.model_dump(exclude_unset=True).keys()),
    )
    service = PeopleService(db)
    person = await service.update(workspace_id, person_id, data)
    logger.info(
        "people.update.completed workspace_id=%s person_id=%s",
        mask_id(str(workspace_id)),
        mask_id(str(person.id)),
    )
    return person


@router.delete("/{person_id}", status_code=204)
async def delete_person(
    person_id: uuid.UUID,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a person."""
    logger.info(
        "people.delete.started workspace_id=%s person_id=%s",
        mask_id(str(workspace_id)),
        mask_id(str(person_id)),
    )
    service = PeopleService(db)
    await service.soft_delete(workspace_id, person_id)
    logger.info(
        "people.delete.completed workspace_id=%s person_id=%s",
        mask_id(str(workspace_id)),
        mask_id(str(person_id)),
    )


@router.post("/{person_id}/snooze", response_model=PersonResponse)
async def snooze_person(
    person_id: uuid.UUID,
    data: SnoozeRequest,
    workspace_id: uuid.UUID = Query(...),
    _workspace: Depends = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Snooze a person until a date."""
    logger.info(
        "people.snooze.started workspace_id=%s person_id=%s until_date=%s",
        mask_id(str(workspace_id)),
        mask_id(str(person_id)),
        data.until_date,
    )
    service = PeopleService(db)
    person = await service.snooze(workspace_id, person_id, data.until_date)
    logger.info(
        "people.snooze.completed workspace_id=%s person_id=%s",
        mask_id(str(workspace_id)),
        mask_id(str(person.id)),
    )
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
    logger.info(
        "people.archive.started workspace_id=%s person_id=%s notes_present=%s",
        mask_id(str(workspace_id)),
        mask_id(str(person_id)),
        bool(data.notes),
    )
    service = PeopleService(db)
    person = await service.archive(workspace_id, person_id)
    logger.info(
        "people.archive.completed workspace_id=%s person_id=%s",
        mask_id(str(workspace_id)),
        mask_id(str(person.id)),
    )
    return person
