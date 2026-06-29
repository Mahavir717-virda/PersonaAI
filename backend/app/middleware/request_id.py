"""Request and correlation ID middleware."""

from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.constants.http import (
    HEADER_CORRELATION_ID,
    HEADER_REQUEST_ID,
    HEADER_USER_ID,
)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach request, correlation, and optional user IDs to each request."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Attach ID values to request state and response headers."""
        request_id = request.headers.get(HEADER_REQUEST_ID) or str(uuid4())
        correlation_id = request.headers.get(HEADER_CORRELATION_ID) or request_id
        user_id = request.headers.get(HEADER_USER_ID)

        request.state.request_id = request_id
        request.state.correlation_id = correlation_id
        request.state.user_id = user_id

        response = await call_next(request)
        response.headers[HEADER_REQUEST_ID] = request_id
        response.headers[HEADER_CORRELATION_ID] = correlation_id
        return response
