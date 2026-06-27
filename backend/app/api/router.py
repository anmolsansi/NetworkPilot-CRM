from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.me import router as me_router
from app.api.routes.workspaces import router as workspaces_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router, tags=["health"])
api_router.include_router(me_router, prefix="/me", tags=["users"])
api_router.include_router(workspaces_router, prefix="/workspaces", tags=["workspaces"])
