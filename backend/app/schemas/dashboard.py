import logging
import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)


class DashboardSummary(BaseModel):
    due_today: int
    overdue: int
    waiting_for_reply: int
    active_total: int


class DuePersonCard(BaseModel):
    id: uuid.UUID
    name: str
    company: str | None
    role: str | None
    linkedin_url: str
    stage: str
    priority: str
    next_action_type: str | None
    next_action_date: date | None
    last_action_type: str | None


class TagDashboardSection(BaseModel):
    id: uuid.UUID
    name: str
    color: str | None
    people_count: int


class DashboardPersonWidget(BaseModel):
    id: uuid.UUID
    name: str
    company: str | None
    role: str | None
    stage: str
    occurred_at: date | datetime | None = None


class DashboardTaskWidget(BaseModel):
    id: uuid.UUID
    person_id: uuid.UUID
    person_name: str
    title: str
    due_date: date


class DashboardImportWidget(BaseModel):
    id: uuid.UUID
    file_name: str | None
    status: str
    total_rows: int
    failed_rows: int
    created_at: datetime


class DashboardWidgets(BaseModel):
    favourites: list[DashboardPersonWidget]
    newly_accepted: list[DashboardPersonWidget]
    stale_relationships: list[DashboardPersonWidget]
    overdue_tasks: list[DashboardTaskWidget]
    recent_imports: list[DashboardImportWidget]


WidgetId = Literal[
    "summary",
    "tags",
    "due",
    "favourites",
    "newly_accepted",
    "stale_relationships",
    "overdue_tasks",
    "recent_imports",
]


class DashboardWidgetConfig(BaseModel):
    id: WidgetId
    visible: bool = True
    limit: int = Field(default=5, ge=1, le=20)


def default_dashboard_widgets() -> list[DashboardWidgetConfig]:
    return [DashboardWidgetConfig(id=widget_id) for widget_id in WidgetId.__args__]


class DashboardConfig(BaseModel):
    version: Literal[1] = 1
    widgets: list[DashboardWidgetConfig] = Field(default_factory=default_dashboard_widgets)

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy(cls, value):
        if isinstance(value, cls):
            return value
        if not value or "widgets" not in value:
            legacy = value or {}
            visibility = {
                "summary": legacy.get("show_summary", True),
                "tags": legacy.get("show_tags", True),
                "due": legacy.get("show_due", True),
            }
            return {
                "version": 1,
                "widgets": [
                    {
                        **widget.model_dump(),
                        "visible": visibility.get(widget.id, widget.visible),
                    }
                    for widget in default_dashboard_widgets()
                ],
            }
        return value

    @model_validator(mode="after")
    def validate_widgets(self):
        configured_ids = {item.id for item in self.widgets}
        if len(configured_ids) != len(self.widgets):
            raise ValueError("Dashboard widgets must be unique.")
        self.widgets.extend(
            item for item in default_dashboard_widgets() if item.id not in configured_ids
        )
        return self

    @classmethod
    def normalize(cls, value):
        return cls.model_validate(value)
