"""Application exception handling package."""

from app.exceptions.base import ApplicationError
from app.exceptions.handlers import register_exception_handlers

__all__ = ["ApplicationError", "register_exception_handlers"]
