import logging

from fastapi import APIRouter

from app.api.routes import (
    activities,
    calendar,
    custom_fields,
    dashboard,
    duplicates,
    exports,
    extension,
    health,
    imports,
    me,
    notifications,
    people,
    pipeline_stages,
    saved_views,
    tags,
    templates,
    workspaces,
)

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(me.router, prefix="/me", tags=["me"])
api_router.include_router(workspaces.router, prefix="/workspaces", tags=["workspaces"])
api_router.include_router(duplicates.router, prefix="/people/duplicates", tags=["duplicates"])
api_router.include_router(people.router, prefix="/people", tags=["people"])
api_router.include_router(activities.router, tags=["activities"])
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(extension.router, prefix="/extension", tags=["extension"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(imports.router, prefix="/imports", tags=["imports"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(exports.router, prefix="/exports", tags=["exports"])
api_router.include_router(
    pipeline_stages.router, prefix="/pipeline-stages", tags=["pipeline-stages"]
)
api_router.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
api_router.include_router(saved_views.router, prefix="/saved-views", tags=["saved_views"])
api_router.include_router(custom_fields.router, prefix="/custom-fields", tags=["custom_fields"])
