"""Database health check helpers."""

import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database.session import async_engine

logger = logging.getLogger(__name__)


async def check_database_connection() -> bool:
    """Return whether the configured database can execute a simple query."""
    try:
        async with async_engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        logger.warning("Database health check failed", exc_info=True)
        return False
