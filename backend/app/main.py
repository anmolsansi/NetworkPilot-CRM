import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.api.router import api_router
from app.core.config import settings
from app.core.errors import (
    AppError,
    app_error_handler,
    general_error_handler,
)
from app.core.logging import get_logger, setup_logging

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Optionally run the durable job pollers inside the web service process."""
    worker_task: asyncio.Task[None] | None = None
    worker_engine = None

    if settings.RUN_EMBEDDED_WORKER:
        from app import worker

        worker_engine = worker.engine
        worker_task = asyncio.create_task(
            worker.run_worker(),
            name="networkpilot-embedded-worker",
        )
        logger.info("embedded_worker.started")

    try:
        yield
    finally:
        if worker_task is not None:
            worker_task.cancel()
            with suppress(asyncio.CancelledError):
                await worker_task

        if worker_engine is not None:
            await worker_engine.dispose()

        if settings.RUN_EMBEDDED_WORKER:
            logger.info("embedded_worker.stopped")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        started_at = time.perf_counter()
        logger.info(
            "request.started request_id=%s method=%s path=%s",
            request_id,
            request.method,
            request.url.path,
        )

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            logger.exception(
                "request.failed request_id=%s method=%s path=%s duration_ms=%s",
                request_id,
                request.method,
                request.url.path,
                duration_ms,
            )
            raise

        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        response.headers["x-request-id"] = request_id
        log_level = logger.warning if response.status_code >= 400 else logger.info
        log_level(
            "request.completed request_id=%s method=%s path=%s status=%s duration_ms=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response


def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title="NetworkPilot API",
        description="Personal CRM for tracking LinkedIn outreach follow-ups",
        version="0.1.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # Exception handlers
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, general_error_handler)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(RequestLoggingMiddleware)

    # API routes
    app.include_router(api_router)

    return app


app = create_app()
