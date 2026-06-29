"""Top-level API router registration."""

from fastapi import APIRouter

from app.api.v1.router import router as v1_router
from app.api.v1.routes.health import router as root_health_router
from app.api.v2.router import router as v2_router
from app.config.config import get_settings

router = APIRouter()
router.include_router(root_health_router)

settings = get_settings()
api_router = APIRouter()
api_router.include_router(v1_router, prefix=settings.api_v1_prefix)
api_router.include_router(v2_router, prefix=settings.api_v2_prefix)
