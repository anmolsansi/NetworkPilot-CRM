import logging
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.logging import get_logger, mask_id
from app.models.user import AppUser
from app.models.workspace import Workspace
from app.schemas.activities import ActivityCreate
from app.schemas.extension import (
    ExtensionLookupResponse,
    ExtensionQuickActionRequest,
    ExtensionQuickActionResponse,
    ExtensionQuickCreateRequest,
    ExtensionQuickCreateResponse,
)
from app.services.activity_service import ActivityService
from app.services.people_service import PeopleService
from app.services.workspace_service import require_workspace_access

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
router = APIRouter()
logger = get_logger(__name__)


@router.get("/extension/lookup", response_model=ExtensionLookupResponse)
async def extension_lookup(
    workspace_id: uuid.UUID = Query(...),
    linkedin_url: str = Query(..., min_length=1),
    workspace: Workspace = Depends(require_workspace_access),
    db: AsyncSession = Depends(get_db),
):
    """Look up a LinkedIn profile in the workspace."""
    from app.services.url_normalizer import normalize_linkedin_url

    logger.info(
        "extension.lookup.started workspace_id=%s url_length=%s",
        mask_id(str(workspace_id)),
        len(linkedin_url),
    )
    # Normalize URL
    result = normalize_linkedin_url(linkedin_url)
    if not result:
        logger.warning(
            "extension.lookup.invalid_url workspace_id=%s url_length=%s",
            mask_id(str(workspace_id)),
            len(linkedin_url),
        )
        return ExtensionLookupResponse(found=False)

    normalized_url, slug = result

    # Search for existing person
    service = PeopleService(db)
    person = await service._find_by_url(workspace_id, normalized_url)

    if person:
        logger.info(
            "extension.lookup.found workspace_id=%s person_id=%s",
            mask_id(str(workspace_id)),
            mask_id(str(person.id)),
        )
        return ExtensionLookupResponse(
            found=True,
            person_id=person.id,
            name=person.name,
            linkedin_url=person.linkedin_url,
            linkedin_slug=person.linkedin_slug,
            stage=person.stage,
            priority=person.priority,
            next_action_type=person.next_action_type,
            next_action_date=person.next_action_date,
            last_action_type=person.last_action_type,
        )

    logger.info(
        "extension.lookup.not_found workspace_id=%s linkedin_slug=%s",
        mask_id(str(workspace_id)),
        slug,
    )
    return ExtensionLookupResponse(
        found=False,
        linkedin_url=normalized_url,
        linkedin_slug=slug,
    )


@router.post("/extension/quick-create", response_model=ExtensionQuickCreateResponse)
async def extension_quick_create(
    data: ExtensionQuickCreateRequest,
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Quick create a person from extension."""
    from app.schemas.people import PersonCreate

    logger.info(
        "extension.quick_create.started workspace_id=%s user_id=%s priority=%s action=%s",
        mask_id(str(data.workspace_id)),
        mask_id(str(user.id)),
        data.priority,
        data.initial_action,
    )
    # Verify workspace access from the body payload
    await require_workspace_access(workspace_id=data.workspace_id, user=user, db=db)

    # Create person
    people_service = PeopleService(db)
    person_data = PersonCreate(
        name=data.name,
        linkedin_url=data.linkedin_url,
        role=data.role,
        company=data.company,
        location=data.location,
        priority=data.priority,
        connection_note=data.connection_note,
        notes=data.notes,
    )
    person = await people_service.create(data.workspace_id, person_data)

    # Create initial activity
    activity_service = ActivityService(db)
    activity_data = ActivityCreate(
        action_type=data.initial_action,
        source="chrome_extension",
        notes=data.notes,
    )
    activity, _ = await activity_service.create(
        workspace_id=data.workspace_id,
        person_id=person.id,
        actor_user_id=user.id,
        data=activity_data,
    )

    logger.info(
        "extension.quick_create.completed workspace_id=%s person_id=%s activity_id=%s",
        mask_id(str(data.workspace_id)),
        mask_id(str(person.id)),
        mask_id(str(activity.id)),
    )
    return ExtensionQuickCreateResponse(
        person_id=person.id,
        name=person.name,
        linkedin_url=person.linkedin_url,
        stage=person.stage,
        next_action_type=person.next_action_type,
        next_action_date=person.next_action_date,
        activity_id=activity.id,
    )


@router.post("/extension/quick-action", response_model=ExtensionQuickActionResponse)
async def extension_quick_action(
    data: ExtensionQuickActionRequest,
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Apply a quick action to an existing person."""
    logger.info(
        "extension.quick_action.started workspace_id=%s person_id=%s user_id=%s action=%s",
        mask_id(str(data.workspace_id)),
        mask_id(str(data.person_id)),
        mask_id(str(user.id)),
        data.action_type,
    )
    # Verify workspace access from the body payload
    await require_workspace_access(workspace_id=data.workspace_id, user=user, db=db)

    activity_service = ActivityService(db)
    activity_data = ActivityCreate(
        action_type=data.action_type,
        source="chrome_extension",
        notes=data.notes,
        next_action_date=data.next_action_date,
        next_action_type=data.next_action_type,
    )

    activity, person = await activity_service.create(
        workspace_id=data.workspace_id,
        person_id=data.person_id,
        actor_user_id=user.id,
        data=activity_data,
    )

    logger.info(
        "extension.quick_action.completed workspace_id=%s person_id=%s activity_id=%s stage=%s",
        mask_id(str(data.workspace_id)),
        mask_id(str(person.id)),
        mask_id(str(activity.id)),
        person.stage,
    )
    return ExtensionQuickActionResponse(
        person_id=person.id,
        stage=person.stage,
        next_action_type=person.next_action_type,
        next_action_date=person.next_action_date,
        activity_id=activity.id,
    )
