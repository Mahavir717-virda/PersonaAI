"""Rate limiter implementation for throttling third-party API requests."""

import asyncio
import time
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token-bucket or window-based rate limiter to protect against third-party API rate limit bans."""

    def __init__(self, max_requests: int = 5, period: float = 1.0) -> None:
        self.max_requests = max_requests
        self.period = period
        self.tokens = max_requests
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire a token, waiting asynchronously if none are available."""
        async with self._lock:
            while True:
                now = time.monotonic()
                passed = now - self.last_update
                
                # Replenish tokens
                self.tokens = min(self.max_requests, self.tokens + passed * (self.max_requests / self.period))
                self.last_update = now

                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return

                # Calculate sleep duration to replenish a token
                needed = 1.0 - self.tokens
                sleep_time = needed / (self.max_requests / self.period)
                logger.info(f"[RateLimiter] Rate limit exceeded, sleeping for {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)

    async def release(self) -> None:
        """Release call hook (if provider releases resources)."""
        pass
