"""FastAPI exception handler registration."""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.constants.messages import HTTP_ERROR, VALIDATION_ERROR
from app.exceptions.base import ApplicationError
from app.schemas.response import ErrorDetail, ErrorResponse


def get_request_id(request: Request) -> str | None:
    """Return the request ID attached by middleware, if present."""
    return getattr(request.state, "request_id", None)


def register_exception_handlers(app: FastAPI) -> None:
    """Register application-wide exception handlers."""

    @app.exception_handler(ApplicationError)
    async def application_exception_handler(
        request: Request,
        exc: ApplicationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                message=exc.message,
                error=exc.error_code,
                details=exc.details,
                request_id=get_request_id(request),
            ).model_dump(mode="json"),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                message=HTTP_ERROR,
                error="http_error",
                details={"detail": exc.detail, "path": request.url.path},
                request_id=get_request_id(request),
            ).model_dump(mode="json"),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        details = [
            ErrorDetail(
                location=list(error.get("loc", [])),
                message=str(error.get("msg", "")),
                error_type=str(error.get("type", "")),
            )
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                message=VALIDATION_ERROR,
                error="validation_error",
                details=details,
                request_id=get_request_id(request),
            ).model_dump(mode="json"),
        )
