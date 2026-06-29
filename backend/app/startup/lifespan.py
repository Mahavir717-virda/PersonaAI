"""FastAPI application lifespan management."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database.session import close_database_connections
from app.startup.state import initialize_runtime_state

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown events."""
    initialize_runtime_state(app)
    logger.info("%s startup complete", app.title)
    try:
        yield
    finally:
        await close_database_connections()
        logger.info("%s shutdown complete", app.title)
