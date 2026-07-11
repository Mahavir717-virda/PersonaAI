"""Database engine construction."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config.settings import Settings


def create_engine(settings: Settings) -> AsyncEngine:
    """Create the async SQLAlchemy engine from application settings."""
    connect_args: dict[str, Any] = {
        "timeout": settings.database_connect_timeout_seconds,
    }
    
    # Cloud PostgreSQL hosts like Neon require SSL
    if "localhost" not in settings.database_url and "127.0.0.1" not in settings.database_url:
        connect_args["ssl"] = True

    return create_async_engine(
        settings.database_url,
        connect_args=connect_args,
        echo=settings.database_echo,
        max_overflow=settings.database_max_overflow,
        pool_pre_ping=True,
        pool_size=settings.database_pool_size,
    )
