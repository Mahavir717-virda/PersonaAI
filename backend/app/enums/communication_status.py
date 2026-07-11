"""Communication status enums."""

from enum import StrEnum


class CommunicationStatus(StrEnum):
    """Normalized status values for communications."""

    NEW = "new"
    READ = "read"
    ARCHIVED = "archived"
    DELETED = "deleted"
    FAILED_IMPORT = "failed_import"
    SYNCING = "syncing"
