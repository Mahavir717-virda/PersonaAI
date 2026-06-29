"""Request timing middleware."""

from time import perf_counter

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.constants.http import HEADER_PROCESS_TIME


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Attach request processing time to HTTP responses."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Measure request processing duration."""
        started_at = perf_counter()
        response = await call_next(request)
        response.headers[HEADER_PROCESS_TIME] = f"{perf_counter() - started_at:.6f}"
        return response
