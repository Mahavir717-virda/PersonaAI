"""Health check helpers for external dependencies."""

import asyncio
import logging
import urllib.error
import urllib.request
from datetime import UTC, datetime

from app.config.settings import Settings

logger = logging.getLogger(__name__)


def format_uptime(started_at: datetime) -> str:
    """Return a compact uptime string from an application start timestamp."""
    uptime = datetime.now(tz=UTC) - started_at
    return str(uptime).split(".", maxsplit=1)[0]


async def check_ollama_health(settings: Settings) -> bool:
    """Return whether the configured Ollama endpoint is reachable."""

    def request_ollama() -> bool:
        url = f"{settings.ollama_base_url.rstrip('/')}{settings.ollama_health_path}"
        try:
            with urllib.request.urlopen(  # noqa: S310
                url,
                timeout=settings.health_check_timeout_seconds,
            ) as response:
                return 200 <= response.status < 500
        except (TimeoutError, urllib.error.URLError, OSError):
            logger.warning("Ollama health check failed", exc_info=True)
            return False

    return await asyncio.to_thread(request_ollama)
