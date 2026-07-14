from datetime import date

from pydantic import BaseModel, ConfigDict


class FunnelMetrics(BaseModel):
    total_saved: int = 0
    contacted: int = 0
    replied: int = 0
    conversion_rate: float = 0.0

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


class WeeklyGoalProgress(BaseModel):
    target: int
    current: int
    percentage: float

    model_config = ConfigDict(from_attributes=True)
