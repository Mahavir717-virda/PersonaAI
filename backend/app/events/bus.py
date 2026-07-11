"""Basic Event Bus implementation."""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Type

logger = logging.getLogger(__name__)


class EventBus:
    """Synchronous & asynchronous in-memory event publishing router."""

    def __init__(self) -> None:
        self._subscribers: Dict[Type[Any], List[Callable[..., Any]]] = {}

    def subscribe(self, event_type: Type[Any], callback: Callable[..., Any]) -> None:
        """Register a subscriber callback for a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        logger.info(f"[EventBus] Subscriber registered for event: {event_type.__name__}")

    async def publish(self, event: Any) -> None:
        """Publish an event to all registered subscriber callbacks."""
        event_type = type(event)
        subscribers = self._subscribers.get(event_type, [])
        if not subscribers:
            return

        logger.info(f"[EventBus] Publishing event {event_type.__name__} to {len(subscribers)} subscribers")
        for callback in subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(
                    f"[EventBus] Error in callback {callback.__name__} for event {event_type.__name__}: {str(e)}",
                    exc_info=True
                )


# Global instance for app-wide event routing
event_bus = EventBus()
