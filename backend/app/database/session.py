"""Async database session management."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config.config import get_settings
from app.database.database import create_engine

settings = get_settings()
async_engine = create_engine(settings)
async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

print("DATABASE_URL =", settings.database_url)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield an async database session for request-scoped dependencies."""
    async with async_session_factory() as session:
        yield session


async def close_database_connections() -> None:
    """Dispose database connections during application shutdown."""
    await async_engine.dispose()
