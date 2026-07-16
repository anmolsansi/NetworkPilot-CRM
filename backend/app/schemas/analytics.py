from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class FunnelStageMetrics(BaseModel):
    key: Literal["saved", "invite_sent", "accepted", "messaged", "replied"]
    label: str
    count: int = 0
    conversion_from_previous: float = 0.0
    conversion_from_saved: float = 0.0


class FunnelMetrics(BaseModel):
    stages: list[FunnelStageMetrics]

    model_config = ConfigDict(from_attributes=True)


class PerformanceBreakdown(BaseModel):
    dimension: str
    dimension_key: str
    dimension_label: str
    sent_count: int = 0
    reply_count: int = 0
    reply_rate: float = 0.0
    date_from: date | None = None
    date_to: date | None = None

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
