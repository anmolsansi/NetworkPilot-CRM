import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundError, ValidationError
from app.core.logging import mask_id
from app.models.person import Person
from app.models.task import Task
from app.models.workspace import WorkspaceMember
from app.schemas.task import TaskCreate, TaskUpdate

_module_logger = logging.getLogger(__name__)


class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _require_workspace_member(
        self, workspace_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        result = await self.db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.deleted_at.is_(None),
            )
        )
        if result.scalar_one_or_none() is None:
            raise ValidationError("Assigned user must be an active member of this workspace.")

    async def _require_person_in_workspace(
        self, workspace_id: uuid.UUID, person_id: uuid.UUID
    ) -> Person:
        result = await self.db.execute(
            select(Person).where(
                Person.id == person_id,
                Person.workspace_id == workspace_id,
                Person.deleted_at.is_(None),
            )
        )
        person = result.scalar_one_or_none()
        if not person:
            raise NotFoundError("Person", str(person_id))
        return person

    async def create(self, workspace_id: uuid.UUID, data: TaskCreate) -> Task:
        _module_logger.info(
            "task_service.create.started workspace_id=%s person_id=%s",
            mask_id(str(workspace_id)),
            mask_id(str(data.person_id)),
        )
        
        await self._require_person_in_workspace(workspace_id, data.person_id)
        
        if data.assigned_to:
            await self._require_workspace_member(workspace_id, data.assigned_to)

        task = Task(
            workspace_id=workspace_id,
            person_id=data.person_id,
            assigned_to=data.assigned_to,
            title=data.title,
            description=data.description,
            due_date=data.due_date,
            status="open",
        )

        self.db.add(task)
        await self.db.flush()
        
        _module_logger.info(
            "task_service.create.completed workspace_id=%s task_id=%s",
            mask_id(str(workspace_id)),
            mask_id(str(task.id)),
        )
        return await self.get(workspace_id, task.id)

    async def get(self, workspace_id: uuid.UUID, task_id: uuid.UUID) -> Task:
        result = await self.db.execute(
            select(Task)
            .where(
                Task.id == task_id,
                Task.workspace_id == workspace_id,
            )
            .options(
                selectinload(Task.person),
                selectinload(Task.assignee),
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            raise NotFoundError("Task", str(task_id))
        return task

    async def update(self, workspace_id: uuid.UUID, task_id: uuid.UUID, data: TaskUpdate) -> Task:
        task = await self.get(workspace_id, task_id)
        update_data = data.model_dump(exclude_unset=True)

        if "assigned_to" in update_data and update_data["assigned_to"]:
            await self._require_workspace_member(workspace_id, update_data["assigned_to"])
            
        if "status" in update_data:
            if update_data["status"] == "completed" and task.status != "completed":
                task.completed_at = datetime.now(timezone.utc)
            elif update_data["status"] == "open" and task.status != "open":
                task.completed_at = None

        for field, value in update_data.items():
            setattr(task, field, value)

        await self.db.flush()
        return await self.get(workspace_id, task.id)

    async def list(
        self,
        workspace_id: uuid.UUID,
        person_id: uuid.UUID | None = None,
        assigned_to: uuid.UUID | None = None,
        status: str | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[list[Task], int]:
        query = select(Task).where(Task.workspace_id == workspace_id).options(
            selectinload(Task.person),
            selectinload(Task.assignee),
        )

        if person_id:
            query = query.where(Task.person_id == person_id)
        if assigned_to:
            query = query.where(Task.assigned_to == assigned_to)
        if status:
            query = query.where(Task.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar()

        offset = (page - 1) * limit
        query = query.order_by(Task.due_date.asc().nullslast(), Task.created_at.desc()).offset(offset).limit(limit)

        result = await self.db.execute(query)
        tasks = result.scalars().all()
        return tasks, total

    async def delete(self, workspace_id: uuid.UUID, task_id: uuid.UUID) -> None:
        task = await self.get(workspace_id, task_id)
        await self.db.delete(task)
        await self.db.flush()
