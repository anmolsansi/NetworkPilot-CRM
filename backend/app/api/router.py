from fastapi import APIRouter

from app.api.routes.activities import router as activities_router
from app.api.routes.calendar import router as calendar_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.exports import router as exports_router
from app.api.routes.extension import router as extension_router
from app.api.routes.health import router as health_router
from app.api.routes.imports import router as imports_router
from app.api.routes.me import router as me_router
from app.api.routes.people import router as people_router
from app.api.routes.templates import router as templates_router
from app.api.routes.workspaces import router as workspaces_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router, tags=["health"])
api_router.include_router(me_router, prefix="/me", tags=["users"])
api_router.include_router(workspaces_router, prefix="/workspaces", tags=["workspaces"])
api_router.include_router(people_router, prefix="/people", tags=["people"])
api_router.include_router(activities_router, tags=["activities"])
api_router.include_router(dashboard_router, tags=["dashboard"])
api_router.include_router(templates_router, prefix="/templates", tags=["templates"])
api_router.include_router(calendar_router, tags=["calendar"])
api_router.include_router(extension_router, tags=["extension"])
api_router.include_router(imports_router, prefix="/imports", tags=["imports"])
api_router.include_router(exports_router, prefix="/exports", tags=["exports"])
