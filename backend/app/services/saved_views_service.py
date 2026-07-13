import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.models.saved_view import SavedPeopleView
from app.schemas.saved_views import SavedViewCreate, SavedViewUpdate


class SavedViewsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self, workspace_id: uuid.UUID, user_id: uuid.UUID) -> list[SavedPeopleView]:
        stmt = (
            select(SavedPeopleView)
            .where(SavedPeopleView.workspace_id == workspace_id)
            .where(SavedPeopleView.user_id == user_id)
            .order_by(SavedPeopleView.name)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self, workspace_id: uuid.UUID, user_id: uuid.UUID, data: SavedViewCreate
    ) -> SavedPeopleView:
        await self._require_unique_name(workspace_id, user_id, data.name)
        view = SavedPeopleView(
            workspace_id=workspace_id,
            user_id=user_id,
            name=data.name,
            filters=data.filters,
            sort_by=data.sort_by,
            sort_order=data.sort_order,
        )
        self.db.add(view)
        await self.db.commit()
        await self.db.refresh(view)
        return view

    async def update(
        self, workspace_id: uuid.UUID, user_id: uuid.UUID, view_id: uuid.UUID, data: SavedViewUpdate
    ) -> SavedPeopleView:
        stmt = (
            select(SavedPeopleView)
            .where(SavedPeopleView.id == view_id)
            .where(SavedPeopleView.workspace_id == workspace_id)
            .where(SavedPeopleView.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        view = result.scalar_one_or_none()

        if not view:
            raise NotFoundError("Saved view", str(view_id))

        update_data = data.model_dump(exclude_unset=True)
        if data.name is not None and data.name != view.name:
            await self._require_unique_name(workspace_id, user_id, data.name, exclude_id=view.id)
        for key, value in update_data.items():
            setattr(view, key, value)

        await self.db.commit()
        await self.db.refresh(view)
        return view

    async def delete(self, workspace_id: uuid.UUID, user_id: uuid.UUID, view_id: uuid.UUID) -> None:
        stmt = (
            select(SavedPeopleView)
            .where(SavedPeopleView.id == view_id)
            .where(SavedPeopleView.workspace_id == workspace_id)
            .where(SavedPeopleView.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        view = result.scalar_one_or_none()

        if not view:
            raise NotFoundError("Saved view", str(view_id))

        await self.db.delete(view)
        await self.db.commit()

    async def _require_unique_name(
        self,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
        name: str,
        exclude_id: uuid.UUID | None = None,
    ) -> None:
        stmt = select(SavedPeopleView.id).where(
            SavedPeopleView.workspace_id == workspace_id,
            SavedPeopleView.user_id == user_id,
            SavedPeopleView.name == name,
        )
        if exclude_id:
            stmt = stmt.where(SavedPeopleView.id != exclude_id)
        if (await self.db.execute(stmt)).scalar_one_or_none() is not None:
            raise ConflictError("A saved view with this name already exists")
