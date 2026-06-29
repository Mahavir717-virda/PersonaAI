"""HTTP request logging middleware."""

import logging
from time import perf_counter

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

logger = logging.getLogger("personaai.requests")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log request method, path, status code, and duration."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Log a single HTTP request lifecycle."""
        started_at = perf_counter()
        response = await call_next(request)
        duration_ms = (perf_counter() - started_at) * 1000
        logger.info(
            "%s %s completed with %s in %.2fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            extra={
                "correlation_id": getattr(request.state, "correlation_id", None),
                "duration_ms": round(duration_ms, 2),
                "request_id": getattr(request.state, "request_id", None),
                "user_id": getattr(request.state, "user_id", None),
            },
        )
        return response
