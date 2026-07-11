"""SQLAlchemy declarative base."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for ORM models."""



# Base class is defined. Models should be imported where needed or in alembic env.py.

