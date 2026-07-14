import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FunnelMetrics(BaseModel):
    total_saved: int = 0
    contacted: int = 0
    replied: int = 0
    conversion_rate: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class TemplatePerformance(BaseModel):
    template_id: uuid.UUID
    template_name: str
    sent_count: int = 0
    reply_count: int = 0
    reply_rate: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class GoalMetricProgress(BaseModel):
    metric: str
    label: str
    target: int
    current: int
    percentage: float


class WeeklyGoalProgress(BaseModel):
    timezone: str
    period_start: datetime
    period_end: datetime
    metrics: list[GoalMetricProgress]

    model_config = ConfigDict(from_attributes=True)
