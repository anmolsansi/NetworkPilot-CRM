import logging
import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationError
from app.core.logging import mask_id
from app.models.activity import Activity
from app.models.person import Person
from app.models.pipeline_stage import PipelineStage
from app.models.tag import Tag
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
        computed_tags = await self._compute_tags(workspace_id, ordered_people, data)
        resolved_stage = await self._resolve_stage(workspace_id, data)
        await self._validate_stage_transitions(workspace_id, ordered_people, resolved_stage)
        for person in ordered_people:
            self._apply_to_person(person, actor_user_id, data, computed_tags, resolved_stage)
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

    async def _compute_tags(
        self, workspace_id: uuid.UUID, people: list[Person], data: BulkPeopleActionRequest
    ) -> dict[uuid.UUID, list[Tag]]:
        if data.action not in {"add_tags", "remove_tags"}:
            return {}

        payload_tags: list[Tag]
        if data.payload.tag_ids is not None:
            tags_result = await self.db.execute(
                select(Tag).where(
                    Tag.id.in_(data.payload.tag_ids), Tag.workspace_id == workspace_id
                )
            )
            payload_tags = list(tags_result.scalars().all())
            if len(payload_tags) != len(data.payload.tag_ids):
                raise NotFoundError("One or more tags")
        else:
            names = data.payload.tags or []
            tags_result = await self.db.execute(
                select(Tag).where(Tag.workspace_id == workspace_id, Tag.name.in_(names))
            )
            by_name = {tag.name: tag for tag in tags_result.scalars().all()}
            if data.action == "add_tags":
                for name in names:
                    if name not in by_name:
                        by_name[name] = Tag(workspace_id=workspace_id, name=name)
                        self.db.add(by_name[name])
                await self.db.flush()
            payload_tags = [by_name[name] for name in names if name in by_name]

        results: dict[uuid.UUID, list[Tag]] = {}
        for person in people:
            current = list(person.tags)
            current_ids = {t.id for t in current}

            if data.action == "add_tags":
                updated = current.copy()
                for t in payload_tags:
                    if t.id not in current_ids:
                        updated.append(t)
                if len(updated) > 20:
                    raise ValidationError("A person can have at most 20 tags.")
            else:
                remove_ids = {tag.id for tag in payload_tags}
                updated = [t for t in current if t.id not in remove_ids]
            results[person.id] = updated
        return results

    async def _resolve_stage(
        self, workspace_id: uuid.UUID, data: BulkPeopleActionRequest
    ) -> tuple[uuid.UUID | None, str | None] | None:
        if data.action != "set_stage":
            return None
        if "stage" in data.payload.model_fields_set:
            return None, data.payload.stage
        if data.payload.stage_id is None:
            return None, None
        result = await self.db.execute(
            select(PipelineStage).where(
                PipelineStage.id == data.payload.stage_id,
                PipelineStage.workspace_id == workspace_id,
            )
        )
        stage = result.scalar_one_or_none()
        if stage is None:
            raise NotFoundError("Pipeline stage", str(data.payload.stage_id))
        return stage.id, stage.name

    async def _validate_stage_transitions(
        self,
        workspace_id: uuid.UUID,
        people: list[Person],
        resolved_stage: tuple[uuid.UUID | None, str | None] | None,
    ) -> None:
        if not resolved_stage or resolved_stage[0] is None:
            return
        target_id = resolved_stage[0]
        source_ids = {person.stage_id for person in people if person.stage_id}
        if not source_ids:
            return
        result = await self.db.execute(
            select(PipelineStage).where(
                PipelineStage.workspace_id == workspace_id,
                PipelineStage.id.in_(source_ids),
            )
        )
        for stage in result.scalars().all():
            if stage.allowed_next_stage_ids and str(target_id) not in stage.allowed_next_stage_ids:
                raise ValidationError(
                    f"The transition from '{stage.name}' to the selected stage is not allowed."
                )

    def _apply_to_person(
        self,
        person: Person,
        actor_user_id: uuid.UUID,
        data: BulkPeopleActionRequest,
        computed_tags: dict[uuid.UUID, list[Tag]],
        resolved_stage: tuple[uuid.UUID | None, str | None] | None,
    ) -> None:
        if data.action == "set_favorite":
            person.is_favorite = data.payload.is_favorite
        elif data.action in {"add_tags", "remove_tags"}:
            person.tags = computed_tags[person.id]
        elif data.action == "set_priority":
            person.priority = data.payload.priority
        elif data.action == "set_stage":
            self._set_stage(person, actor_user_id, data, resolved_stage)
        elif data.action == "archive":
            self._archive(person, actor_user_id)
        elif data.action == "set_next_action":
            person.next_action_type = data.payload.next_action_type
            person.next_action_date = data.payload.next_action_date

    def _set_stage(
        self,
        person: Person,
        actor_user_id: uuid.UUID,
        data: BulkPeopleActionRequest,
        resolved_stage: tuple[uuid.UUID | None, str | None] | None,
    ) -> None:
        stage_id, stage_name = resolved_stage or (None, None)
        legacy_stage = data.payload.stage if "stage" in data.payload.model_fields_set else None
        target_status = "archived" if legacy_stage == "archived" else "active"
        changed = person.stage_id != stage_id or person.status != target_status
        if legacy_stage is not None:
            changed = changed or person.stage != legacy_stage
        if not changed:
            return
        previous_stage = str(person.stage_id) if person.stage_id else person.stage
        person.stage_id = stage_id
        if legacy_stage is not None:
            person.stage = legacy_stage
        person.status = target_status
        if target_status == "archived":
            person.next_action_type = None
            person.next_action_date = None
        new_stage = legacy_stage or stage_name or "None"
        self._record_activity(
            person,
            actor_user_id,
            "bulk_stage_change",
            previous_stage,
            new_stage,
            "Bulk stage change",
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
