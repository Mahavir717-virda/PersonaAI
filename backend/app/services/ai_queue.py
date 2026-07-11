"""AI Queue worker interface definition."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class AIQueue:
    """Queues message objects for async processing (summaries, task extractions) without blocking sync passes."""

    async def enqueue_task(self, message_id: str, payload: dict[str, Any]) -> None:
        """Enqueue task parameters to async Celery/Arq workers."""
        logger.info(f"[AIQueue] Enqueued message {message_id} to background processing pipeline.")
