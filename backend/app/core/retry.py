"""Async retry helpers with exponential backoff and jitter."""

import asyncio
import random
import logging
from typing import Any, Callable, Coroutine, TypeVar
from functools import wraps

import httpx

from app.config.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

T = TypeVar("T")

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def http_retry(
    max_retries: int = settings.gmail_max_retries,
    initial_backoff: float = settings.gmail_initial_backoff_seconds,
    max_backoff: float = settings.gmail_max_backoff_seconds,
) -> Callable[
    [Callable[..., Coroutine[Any, Any, T]]], Callable[..., Coroutine[Any, Any, T]]
]:
    """Decorate an async function to retry on specific HTTP status codes."""

    def decorator(
        func: Callable[..., Coroutine[Any, Any, T]]
    ) -> Callable[..., Coroutine[Any, Any, T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            """Execute the decorated coroutine with retry logic."""
            backoff = initial_backoff
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except httpx.HTTPStatusError as e:
                    if e.response.status_code not in RETRYABLE_STATUS_CODES:
                        raise

                    if attempt == max_retries - 1:
                        logger.error(
                            "Retry limit exceeded for %s after %d attempts",
                            func.__name__,
                            max_retries,
                        )
                        raise

                    retry_after_header = e.response.headers.get("Retry-After")
                    if retry_after_header:
                        try:
                            wait_time = int(retry_after_header)
                            logger.info(
                                "Respecting Retry-After header: waiting %d seconds",
                                wait_time,
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        except (ValueError, TypeError):
                            logger.warning(
                                "Invalid Retry-After header format: %s",
                                retry_after_header,
                            )

                    # Exponential backoff with jitter
                    jitter = random.uniform(0, backoff * 0.1)
                    sleep_duration = min(backoff + jitter, max_backoff)
                    logger.info(
                        "Attempt %d/%d failed for %s. Retrying in %.2f seconds...",
                        attempt + 1,
                        max_retries,
                        func.__name__,
                        sleep_duration,
                    )
                    await asyncio.sleep(sleep_duration)
                    backoff *= 2
            # This line should not be reachable due to the raise in the loop
            raise RuntimeError("Retry logic failed unexpectedly")

        return wrapper

    return decorator