import logging
import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationError
from app.core.logging import mask_id
from app.models.activity import Activity
from app.models.person import Person
from app.schemas.people import BulkPeopleActionRequest

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)


class BulkPeopleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def apply(
        self,
        workspace_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        data: BulkPeopleActionRequest,
    ) -> list[Person]:
        _module_logger.info(
            "bulk_people_service.apply.started workspace_id=%s action=%s count=%s",
            mask_id(str(workspace_id)),
            data.action,
            len(data.person_ids),
        )
        ordered_people = await self._load_people(workspace_id, data.person_ids)
        computed_tags = self._compute_tags(ordered_people, data)
        for person in ordered_people:
            self._apply_to_person(person, actor_user_id, data, computed_tags)
        await self.db.flush()
        ordered_people = await self._load_people(workspace_id, data.person_ids)
        _module_logger.info(
            "bulk_people_service.apply.completed workspace_id=%s action=%s count=%s",
            mask_id(str(workspace_id)),
            data.action,
            len(ordered_people),
        )
        return ordered_people

    async def _load_people(
        self, workspace_id: uuid.UUID, person_ids: list[uuid.UUID]
    ) -> list[Person]:
        result = await self.db.execute(
            select(Person).where(
                Person.id.in_(person_ids),
                Person.workspace_id == workspace_id,
                Person.deleted_at.is_(None),
            )
        )
        people_by_id = {person.id: person for person in result.scalars().all()}
        if len(people_by_id) != len(person_ids):
            raise NotFoundError("One or more people")
        return [people_by_id[person_id] for person_id in person_ids]

    def _compute_tags(
        self, people: list[Person], data: BulkPeopleActionRequest
    ) -> dict[uuid.UUID, list[str]]:
        if data.action not in {"add_tags", "remove_tags"}:
            return {}
        results: dict[uuid.UUID, list[str]] = {}
        for person in people:
            current = list(person.tags or [])
            if data.action == "add_tags":
                updated = current + [tag for tag in data.payload.tags if tag not in current]
                if len(updated) > 20:
                    raise ValidationError("A person can have at most 20 tags.")
            else:
                removed = set(data.payload.tags)
                updated = [tag for tag in current if tag not in removed]
            results[person.id] = updated
        return results

    def _apply_to_person(
        self,
        person: Person,
        actor_user_id: uuid.UUID,
        data: BulkPeopleActionRequest,
        computed_tags: dict[uuid.UUID, list[str]],
    ) -> None:
        if data.action == "set_favorite":
            person.is_favorite = data.payload.is_favorite
        elif data.action in {"add_tags", "remove_tags"}:
            person.tags = computed_tags[person.id] or None
        elif data.action == "set_priority":
            person.priority = data.payload.priority
        elif data.action == "set_stage":
            self._set_stage(person, actor_user_id, data.payload.stage)
        elif data.action == "archive":
            self._archive(person, actor_user_id)
        elif data.action == "set_next_action":
            person.next_action_type = data.payload.next_action_type
            person.next_action_date = data.payload.next_action_date

    def _set_stage(self, person: Person, actor_user_id: uuid.UUID, stage: str) -> None:
        target_status = "archived" if stage == "archived" else "active"
        clears_next_action = stage == "archived"
        changed = (
            person.stage != stage
            or person.status != target_status
            or (
                clears_next_action
                and (person.next_action_type is not None or person.next_action_date is not None)
            )
        )
        if not changed:
            return
        previous_stage = person.stage
        person.stage = stage
        person.status = target_status
        if clears_next_action:
            person.next_action_type = None
            person.next_action_date = None
        self._record_activity(
            person, actor_user_id, "bulk_stage_change", previous_stage, stage, "Bulk stage change"
        )

    def _archive(self, person: Person, actor_user_id: uuid.UUID) -> None:
        changed = (
            person.stage != "archived"
            or person.status != "archived"
            or person.next_action_type is not None
            or person.next_action_date is not None
        )
        if not changed:
            return
        previous_stage = person.stage
        person.stage = "archived"
        person.status = "archived"
        person.next_action_type = None
        person.next_action_date = None
        self._record_activity(
            person, actor_user_id, "bulk_archive", previous_stage, "archived", "Bulk archive"
        )

    def _record_activity(
        self,
        person: Person,
        actor_user_id: uuid.UUID,
        action_type: str,
        previous_stage: str,
        new_stage: str,
        notes: str,
    ) -> None:
        person.last_action_type = action_type
        person.last_action_date = date.today()
        self.db.add(
            Activity(
                person_id=person.id,
                workspace_id=person.workspace_id,
                actor_user_id=actor_user_id,
                action_type=action_type,
                source="web_app",
                previous_stage=previous_stage,
                new_stage=new_stage,
                notes=notes,
            )
        )
