"""Webhook routing manager implementation."""

import logging
from typing import Dict, Type
from app.webhooks.base import BaseWebhookHandler

logger = logging.getLogger(__name__)


class WebhookManager:
    """Manages discoverability and routing of incoming webhooks to platform handlers."""

    _handlers: Dict[str, Type[BaseWebhookHandler]] = {}

    @classmethod
    def register_handler(cls, platform: str, handler_cls: Type[BaseWebhookHandler]) -> None:
        """Register a handler class for a communication provider."""
        cls._handlers[platform.upper()] = handler_cls
        logger.info(f"Registered webhook handler for platform: '{platform}'")

    @classmethod
    def get_handler(cls, platform: str) -> Type[BaseWebhookHandler] | None:
        """Retrieve a registered handler class."""
        return cls._handlers.get(platform.upper())
