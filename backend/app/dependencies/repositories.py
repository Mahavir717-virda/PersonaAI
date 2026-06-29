"""Repository dependency helpers."""

from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository

RepositoryT = TypeVar("RepositoryT", bound=BaseRepository)


def build_repository(
    repository_type: type[RepositoryT],
    session: AsyncSession,
    *args: object,
    **kwargs: object,
) -> RepositoryT:
    """Build a repository with the current request database session."""
    return repository_type(session, *args, **kwargs)
