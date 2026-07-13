import logging

from pydantic import BaseModel

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)


class CalendarLinkResponse(BaseModel):
    url: str
    title: str
    description: str
