import logging
import uuid
from datetime import date

from pydantic import BaseModel

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
