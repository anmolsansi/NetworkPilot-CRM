import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, ErrorCode
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

    async def create(self, workspace_id: uuid.UUID, user_id: uuid.UUID, data: SavedViewCreate) -> SavedPeopleView:
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
            raise AppError(ErrorCode.NOT_FOUND, "Saved view not found")

        update_data = data.model_dump(exclude_unset=True)
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
            raise AppError(ErrorCode.NOT_FOUND, "Saved view not found")

        await self.db.delete(view)
        await self.db.commit()
