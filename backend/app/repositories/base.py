"""Base repository contract for future persistence objects."""

from abc import ABC
from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(ABC, Generic[ModelT]):
    """Base class for repositories that use an async database session."""

    def __init__(self, session: AsyncSession, model: type[ModelT]) -> None:
        """Initialize the repository with a session and model type."""
        self._session = session
        self._model = model

    @property
    def session(self) -> AsyncSession:
        """Return the repository database session."""
        return self._session

    @property
    def model(self) -> type[ModelT]:
        """Return the SQLAlchemy model managed by the repository."""
        return self._model
