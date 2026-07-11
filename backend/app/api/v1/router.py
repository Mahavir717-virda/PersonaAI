"""Version 1 API router registration."""

from fastapi import APIRouter

from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.users import router as users_router
from app.api.v1.routes.connectors import router as connectors_router
from app.api.v1.routes.communications import router as communications_router
from app.api.v1.routes.extension import router as extension_router
from app.api.v1.routes.models import router as models_router
from app.api.v1.routes.brain import router as brain_router
from app.api.v1.routes.chat import router as chat_router

router = APIRouter()
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(connectors_router)
router.include_router(communications_router)
router.include_router(extension_router)
router.include_router(models_router)
router.include_router(brain_router)
router.include_router(chat_router)

