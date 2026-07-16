import logging
import uuid
from datetime import datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.dashboard import DashboardConfig

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    default_follow_up_delay_days: int = Field(default=3, ge=1, le=30)
    default_acceptance_check_delay_days: int = Field(default=1, ge=1, le=14)
    timezone: str = Field(default="UTC", max_length=50)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Unknown timezone.") from exc
        return value


class WorkspaceUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    default_follow_up_delay_days: int | None = Field(None, ge=1, le=30)
    default_acceptance_check_delay_days: int | None = Field(None, ge=1, le=14)
    daily_reminder_time: str | None = Field(None, pattern=r"^\d{2}:\d{2}$")
    timezone: str | None = Field(None, max_length=50)
    quiet_hours_start: str | None = Field(None, pattern=r"^\d{2}:\d{2}$")
    quiet_hours_end: str | None = Field(None, pattern=r"^\d{2}:\d{2}$")
    email_reminders_enabled: bool | None = None
    daily_digest_enabled: bool | None = None
    overdue_alerts_enabled: bool | None = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        if value is not None:
            WorkspaceCreate.validate_timezone(value)
        return value

    @model_validator(mode="after")
    def validate_quiet_hours(self):
        if (self.quiet_hours_start is None) != (self.quiet_hours_end is None):
            raise ValueError("Quiet hours require both a start and end time.")
        return self


class WorkspaceResponse(BaseModel):
    id: uuid.UUID
    name: str
    owner_id: uuid.UUID
    default_follow_up_delay_days: int
    default_acceptance_check_delay_days: int
    daily_reminder_time: time
    timezone: str
    quiet_hours_start: time | None
    quiet_hours_end: time | None
    email_reminders_enabled: bool
    daily_digest_enabled: bool
    overdue_alerts_enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkspaceMemberUpdate(BaseModel):
    dashboard_config: DashboardConfig | None = None
    weekly_outreach_target: int | None = None
    weekly_goals: "WeeklyGoals | None" = None


class WeeklyGoals(BaseModel):
    profiles_added: int = Field(default=25, ge=0, le=10000)
    invitations_sent: int = Field(default=50, ge=0, le=10000)
    follow_ups_sent: int = Field(default=25, ge=0, le=10000)
    replies_received: int = Field(default=10, ge=0, le=10000)


class WorkspaceMemberResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    dashboard_config: DashboardConfig
    weekly_outreach_target: int
    weekly_goals: WeeklyGoals
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("dashboard_config", mode="before")
    @classmethod
    def normalize_dashboard_config(cls, value):
        return DashboardConfig.normalize(value)


class WorkspaceMemberDirectoryEntry(BaseModel):
    user_id: uuid.UUID
    email: str
    display_name: str | None
    role: str
