import logging
import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.logging import mask_id
from app.models.activity import Activity
from app.models.person import Person
from app.models.workspace import Workspace
from app.schemas.activities import ActivityCreate
from app.services.transition_service import calculate_transition

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)


class ActivityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        workspace_id: uuid.UUID,
        person_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        data: ActivityCreate,
    ) -> tuple[Activity, Person]:
        """
        Create an activity and update person state in one transaction.

        Returns:
            Tuple of (created activity, updated person)
        """
        _module_logger.info(
            "activity_service.create.started "
            "workspace_id=%s person_id=%s actor_user_id=%s action=%s",
            mask_id(str(workspace_id)),
            mask_id(str(person_id)),
            mask_id(str(actor_user_id)),
            data.action_type,
        )
        # Load person with workspace check
        result = await self.db.execute(
            select(Person).where(
                Person.id == person_id,
                Person.workspace_id == workspace_id,
                Person.deleted_at.is_(None),
            )
        )
        person = result.scalar_one_or_none()
        if not person:
            _module_logger.warning(
                "activity_service.create.person_missing workspace_id=%s person_id=%s",
                mask_id(str(workspace_id)),
                mask_id(str(person_id)),
            )
            raise NotFoundError("Person", str(person_id))

        # Capture previous stage
        previous_stage = person.stage

        # Calculate transition
        workspace_result = await self.db.execute(
            select(Workspace).where(Workspace.id == workspace_id)
        )
        workspace = workspace_result.scalar_one()

        transition = calculate_transition(
            action_type=data.action_type,
            follow_up_delay_days=workspace.default_follow_up_delay_days,
            acceptance_check_delay_days=workspace.default_acceptance_check_delay_days,
            override_next_action_date=data.next_action_date,
            override_next_action_type=data.next_action_type,
        )

        # Create activity
        activity = Activity(
            person_id=person_id,
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action_type=data.action_type,
            source=data.source,
            previous_stage=previous_stage,
            new_stage=transition.new_stage,
            message=data.message,
            notes=data.notes,
        )
        self.db.add(activity)

        # Update person state
        person.stage = transition.new_stage
        person.last_action_type = data.action_type
        person.last_action_date = date.today()
        person.next_action_type = transition.next_action_type
        person.next_action_date = transition.next_action_date

        await self.db.flush()
        _module_logger.info(
            "activity_service.create.completed "
            "workspace_id=%s person_id=%s activity_id=%s old_stage=%s new_stage=%s",
            mask_id(str(workspace_id)),
            mask_id(str(person_id)),
            mask_id(str(activity.id)),
            previous_stage,
            person.stage,
        )

        return activity, person

    async def list(
        self,
        workspace_id: uuid.UUID,
        person_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Activity]:
        """List activities for a person in newest-first order."""
        _module_logger.info(
            "activity_service.list.started workspace_id=%s person_id=%s limit=%s offset=%s",
            mask_id(str(workspace_id)),
            mask_id(str(person_id)),
            limit,
            offset,
        )
        # Verify person belongs to workspace
        person_result = await self.db.execute(
            select(Person).where(
                Person.id == person_id,
                Person.workspace_id == workspace_id,
                Person.deleted_at.is_(None),
            )
        )
        if not person_result.scalar_one_or_none():
            _module_logger.warning(
                "activity_service.list.person_missing workspace_id=%s person_id=%s",
                mask_id(str(workspace_id)),
                mask_id(str(person_id)),
            )
            raise NotFoundError("Person", str(person_id))

        result = await self.db.execute(
            select(Activity)
            .where(Activity.person_id == person_id)
            .order_by(Activity.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        activities = result.scalars().all()
        _module_logger.info(
            "activity_service.list.completed workspace_id=%s person_id=%s count=%s",
            mask_id(str(workspace_id)),
            mask_id(str(person_id)),
            len(activities),
        )
        return activities
