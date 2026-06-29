"""Base service contract for future business workflows."""

import logging
from abc import ABC


class BaseService(ABC):
    """Base class for services that own business workflow orchestration."""

    def __init__(self) -> None:
        """Initialize a service-scoped logger."""
        self._logger = logging.getLogger(self.__class__.__module__)

    @property
    def logger(self) -> logging.Logger:
        """Return the service logger."""
        return self._logger
