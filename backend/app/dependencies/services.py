"""Service dependency helpers."""

from typing import TypeVar

from app.services.base import BaseService

ServiceT = TypeVar("ServiceT", bound=BaseService)


def build_service(
    service_type: type[ServiceT],
    *args: object,
    **kwargs: object,
) -> ServiceT:
    """Build a service instance for dependency injection."""
    return service_type(*args, **kwargs)
