import uuid
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


class TemplatePerformance(BaseModel):
    template_id: uuid.UUID
    template_name: str
    sent_count: int = 0
    reply_count: int = 0
    reply_rate: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class WeeklyGoalProgress(BaseModel):
    target: int
    current: int
    percentage: float

    model_config = ConfigDict(from_attributes=True)
