"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router, router
from app.config.config import get_settings
from app.core import metadata
from app.exceptions import register_exception_handlers
from app.logging import configure_logging
from app.middleware import (
    ExceptionMiddleware,
    RequestIDMiddleware,
    RequestLoggingMiddleware,
    RequestTimingMiddleware,
)
from app.startup import lifespan
from app.startup.state import initialize_runtime_state


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    configure_logging(settings)

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        description=metadata.DESCRIPTION,
        contact={"name": metadata.AUTHOR},
        license_info={"name": metadata.LICENSE, "identifier": "MIT"},
        openapi_tags=metadata.OPENAPI_TAGS,
    )
    initialize_runtime_state(application)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
        expose_headers=settings.cors_expose_headers,
    )
    application.add_middleware(ExceptionMiddleware)
    application.add_middleware(RequestTimingMiddleware)
    application.add_middleware(RequestLoggingMiddleware)
    application.add_middleware(RequestIDMiddleware)

    register_exception_handlers(application)
    application.include_router(router)
    application.include_router(api_router)

    return application


app = create_app()
