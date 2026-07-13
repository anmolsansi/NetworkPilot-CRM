import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.tag import Tag
from app.models.user import AppUser
from app.schemas.tag import TagCreate, TagResponse, TagUpdate
from app.services.workspace_service import require_workspace_access

router = APIRouter()


@router.get("", response_model=list[TagResponse])
async def list_tags(
    workspace_id: uuid.UUID,
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_workspace_access(workspace_id, user, db)
    stmt = select(Tag).where(Tag.workspace_id == workspace_id).order_by(Tag.name)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("", response_model=TagResponse)
async def create_tag(
    tag_in: TagCreate,
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_workspace_access(tag_in.workspace_id, user, db)

    tag = Tag(workspace_id=tag_in.workspace_id, name=tag_in.name.strip(), color=tag_in.color)
    db.add(tag)
    try:
        await db.commit()
        await db.refresh(tag)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail="Tag with this name already exists in the workspace"
        )

    return tag


@router.patch("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: uuid.UUID,
    tag_in: TagUpdate,
    workspace_id: uuid.UUID,
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_workspace_access(workspace_id, user, db)
    tag = await db.get(Tag, tag_id)
    if not tag or tag.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Tag not found")
    for field, value in tag_in.model_dump(exclude_unset=True).items():
        setattr(tag, field, value.strip() if field == "name" and value else value)
    try:
        await db.commit()
        await db.refresh(tag)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400, detail="Tag with this name already exists in the workspace"
        )
    return tag


@router.delete("/{tag_id}", status_code=204)
async def delete_tag(
    tag_id: uuid.UUID,
    workspace_id: uuid.UUID,
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_workspace_access(workspace_id, user, db)
    tag = await db.get(Tag, tag_id)
    if not tag or tag.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Tag not found")

    await db.delete(tag)
    await db.commit()
    return None
