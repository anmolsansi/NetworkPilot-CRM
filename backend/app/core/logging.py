import logging
import sys

from app.core.config import settings

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
def setup_logging() -> None:
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True,
    )

    # Reduce noise from third-party libraries
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def mask_id(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 8:
        return value
    return f"...{value[-8:]}"
