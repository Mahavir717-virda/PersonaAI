"""Middleware for unexpected exception responses."""

import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.constants.messages import INTERNAL_SERVER_ERROR
from app.schemas.response import ErrorResponse

logger = logging.getLogger(__name__)


class ExceptionMiddleware(BaseHTTPMiddleware):
    """Convert unhandled exceptions into consistent JSON responses."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Handle unhandled exceptions raised by downstream handlers."""
        try:
            return await call_next(request)
        except Exception:
            logger.exception("Unhandled application exception")
            request_id = getattr(request.state, "request_id", None)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=ErrorResponse(
                    message=INTERNAL_SERVER_ERROR,
                    error="internal_server_error",
                    details={"path": request.url.path},
                    request_id=request_id,
                ).model_dump(mode="json"),
            )
