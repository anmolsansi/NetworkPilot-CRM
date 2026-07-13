import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError, ValidationError
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
        await CustomFieldService._require_unique_name(db, workspace_id, data.name.strip())
        field = CustomField(
            workspace_id=workspace_id,
            name=data.name.strip(),
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
        if "name" in update_data:
            update_data["name"] = update_data["name"].strip()
            await CustomFieldService._require_unique_name(
                db, workspace_id, update_data["name"], exclude_id=field.id
            )
        if "options" in update_data and field.field_type == "select":
            choices = (update_data["options"] or {}).get("choices", [])
            if not choices or len(choices) != len(set(choices)):
                raise ValidationError("Select fields need unique choices.")
        for key, value in update_data.items():
            setattr(field, key, value)

        await db.commit()
        await db.refresh(field)
        return field

    @staticmethod
    async def delete(db: AsyncSession, field_id: uuid.UUID, workspace_id: uuid.UUID) -> None:
        field = await CustomFieldService.get_by_id(db, field_id, workspace_id)
        await db.delete(field)
        await db.commit()

    @staticmethod
    async def _require_unique_name(
        db: AsyncSession,
        workspace_id: uuid.UUID,
        name: str,
        exclude_id: uuid.UUID | None = None,
    ) -> None:
        stmt = select(CustomField.id).where(
            CustomField.workspace_id == workspace_id,
            CustomField.name == name,
        )
        if exclude_id:
            stmt = stmt.where(CustomField.id != exclude_id)
        if (await db.execute(stmt)).scalar_one_or_none() is not None:
            raise ConflictError("A custom field with this name already exists")
