import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.custom_field import CustomField
from app.schemas.custom_field import CustomFieldCreate, CustomFieldUpdate

class CustomFieldService:
    @staticmethod
    async def get_by_id(
        db: AsyncSession, field_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> CustomField:
        stmt = select(CustomField).where(
            CustomField.id == field_id, CustomField.workspace_id == workspace_id
        )
        result = await db.execute(stmt)
        field = result.scalar_one_or_none()
        if not field:
            raise NotFoundError("CustomField", str(field_id))
        return field

    @staticmethod
    async def get_all_for_workspace(
        db: AsyncSession, workspace_id: uuid.UUID
    ) -> Sequence[CustomField]:
        stmt = (
            select(CustomField)
            .where(CustomField.workspace_id == workspace_id)
            .order_by(CustomField.created_at.asc())
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def create(
        db: AsyncSession, workspace_id: uuid.UUID, data: CustomFieldCreate
    ) -> CustomField:
        field = CustomField(
            workspace_id=workspace_id,
            name=data.name,
            field_type=data.field_type,
            options=data.options,
        )
        db.add(field)
        await db.commit()
        await db.refresh(field)
        return field

    @staticmethod
    async def update(
        db: AsyncSession, field_id: uuid.UUID, workspace_id: uuid.UUID, data: CustomFieldUpdate
    ) -> CustomField:
        field = await CustomFieldService.get_by_id(db, field_id, workspace_id)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(field, key, value)

        await db.commit()
        await db.refresh(field)
        return field

    @staticmethod
    async def delete(
        db: AsyncSession, field_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> None:
        field = await CustomFieldService.get_by_id(db, field_id, workspace_id)
        await db.delete(field)
        await db.commit()
