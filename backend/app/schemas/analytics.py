import uuid
from typing import Dict

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


class WeeklyGoalProgress(BaseModel):
    target: int
    current: int
    percentage: float

    model_config = ConfigDict(from_attributes=True)
