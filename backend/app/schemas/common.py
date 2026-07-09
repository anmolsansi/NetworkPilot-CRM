import logging

from pydantic import BaseModel

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class SuccessResponse(BaseModel):
    message: str
