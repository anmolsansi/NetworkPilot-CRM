import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.models.template import MessageTemplate
from app.schemas.templates import TemplateCreate, TemplateUpdate


class TemplateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(
        self, workspace_id: uuid.UUID, category: str | None = None
    ) -> list[MessageTemplate]:
        """List templates in workspace."""
        query = select(MessageTemplate).where(
            MessageTemplate.workspace_id == workspace_id,
            MessageTemplate.deleted_at.is_(None),
        )
        if category:
            query = query.where(MessageTemplate.category == category)
        query = query.order_by(MessageTemplate.name)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get(
        self, workspace_id: uuid.UUID, template_id: uuid.UUID
    ) -> MessageTemplate:
        """Get a template by ID."""
        result = await self.db.execute(
            select(MessageTemplate).where(
                MessageTemplate.id == template_id,
                MessageTemplate.workspace_id == workspace_id,
                MessageTemplate.deleted_at.is_(None),
            )
        )
        template = result.scalar_one_or_none()
        if not template:
            raise NotFoundError("Template", str(template_id))
        return template

    async def create(
        self, workspace_id: uuid.UUID, data: TemplateCreate
    ) -> MessageTemplate:
        """Create a template."""
        # Check for duplicate name
        existing = await self._find_by_name(workspace_id, data.name)
        if existing:
            raise ConflictError("A template with this name already exists")

        template = MessageTemplate(
            workspace_id=workspace_id,
            name=data.name,
            category=data.category,
            body=data.body,
            variables=data.variables,
        )
        self.db.add(template)
        await self.db.flush()
        return template

    async def update(
        self, workspace_id: uuid.UUID, template_id: uuid.UUID, data: TemplateUpdate
    ) -> MessageTemplate:
        """Update a template."""
        template = await self.get(workspace_id, template_id)

        update_data = data.model_dump(exclude_unset=True)

        # Check name uniqueness if changing
        if "name" in update_data and update_data["name"] != template.name:
            existing = await self._find_by_name(workspace_id, update_data["name"])
            if existing:
                raise ConflictError("A template with this name already exists")

        for field, value in update_data.items():
            setattr(template, field, value)

        await self.db.flush()
        return template

    async def delete(self, workspace_id: uuid.UUID, template_id: uuid.UUID) -> None:
        """Soft delete a template."""
        template = await self.get(workspace_id, template_id)
        from datetime import datetime, timezone
        template.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def seed_defaults(self, workspace_id: uuid.UUID) -> None:
        """Seed default templates for a workspace."""
        defaults = [
            {
                "name": "Connection Request",
                "category": "connection_request",
                "body": "Hi {{first_name}}, I'd love to connect and learn more about your work at {{company}}.",
                "variables": ["first_name", "company"],
                "is_default": True,
            },
            {
                "name": "First Message",
                "category": "first_message",
                "body": "Thanks for connecting, {{first_name}}! I've been following your work at {{company}} and would love to chat about {{role}}.",
                "variables": ["first_name", "company", "role"],
                "is_default": True,
            },
            {
                "name": "Follow Up",
                "category": "follow_up",
                "body": "Hi {{first_name}}, just checking in on my previous message. Would love to connect when you have a moment.",
                "variables": ["first_name"],
                "is_default": True,
            },
        ]

        for template_data in defaults:
            existing = await self._find_by_name(workspace_id, template_data["name"])
            if not existing:
                template = MessageTemplate(
                    workspace_id=workspace_id,
                    **template_data,
                )
                self.db.add(template)

        await self.db.flush()

    async def _find_by_name(
        self, workspace_id: uuid.UUID, name: str
    ) -> MessageTemplate | None:
        """Find a template by name in workspace."""
        result = await self.db.execute(
            select(MessageTemplate).where(
                MessageTemplate.workspace_id == workspace_id,
                MessageTemplate.name == name,
                MessageTemplate.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()
