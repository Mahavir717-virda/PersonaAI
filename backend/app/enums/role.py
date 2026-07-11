"""User role enums."""

from enum import StrEnum


class UserRole(StrEnum):
    """Roles for authorization."""

    USER = "user"
    ADMIN = "admin"
