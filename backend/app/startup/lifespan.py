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
    logger.info("Initializing local AI Summary model...")
    try:
        from app.brain.summary.loader import SummaryModelLoader
        loader = SummaryModelLoader()
        loader.load()
        if loader.health_check():
            logger.info("Model warmup: testing inference...")
            try:
                import torch
                inputs = torch.tensor([[101, 102]])
                loader.model.generate(inputs, max_new_tokens=5)
            except Exception as warmup_err:
                logger.warning("Model warmup warning (non-fatal): %s", str(warmup_err))
            logger.info("Local AI Summary model loaded and ready!")
    except Exception as e:
        logger.error("Failed to warm up local AI Summary model: %s", str(e))
    logger.info("%s startup complete", app.title)
    try:
        yield
    finally:
        await close_database_connections()
        logger.info("%s shutdown complete", app.title)
