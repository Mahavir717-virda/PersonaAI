"""Health check routes for platform availability."""

from fastapi import APIRouter, Request, status

from app.config.config import get_settings
from app.constants.messages import HEALTH_CHECK_SUCCESSFUL
from app.core.health import check_ollama_health, format_uptime
from app.database.checks import check_database_connection
from app.schemas.health import HealthStatus
from app.schemas.response import ApiResponse
from app.startup.state import get_runtime_state

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=ApiResponse[HealthStatus],
    status_code=status.HTTP_200_OK,
    summary="Check application health",
)
async def health_check(request: Request) -> ApiResponse[HealthStatus]:
    """Return application and dependency health details."""
    settings = get_settings()
    runtime_state = get_runtime_state(request.app)

    try:
        database_connected = await check_database_connection()
    except Exception:
        database_connected = False

    try:
        ollama_running = await check_ollama_health(settings)
    except Exception:
        ollama_running = False

    health_status = HealthStatus(
        status="healthy" if database_connected and ollama_running else "degraded",
        database="connected" if database_connected else "unavailable",
        ollama="running" if ollama_running else "unavailable",
        version=settings.app_version,
        uptime=format_uptime(runtime_state.started_at),
    )
    return ApiResponse(
        success=True,
        message=HEALTH_CHECK_SUCCESSFUL,
        data=health_status,
    )
