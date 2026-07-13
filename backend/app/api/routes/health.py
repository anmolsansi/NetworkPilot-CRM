import logging

from fastapi import APIRouter

from app.core.logging import get_logger

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
router = APIRouter()
logger = get_logger(__name__)


@router.get("")
async def health():
    logger.debug("health.check")
    return {"status": "ok", "service": "networkpilot-api"}
