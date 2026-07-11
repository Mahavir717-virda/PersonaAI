"""Rate limiting helper."""

import time
from fastapi import Request
from app.exceptions.authentication import AuthorizationError


class RateLimiter:
    """Simple in-memory sliding window rate limiter."""

    def __init__(self, limit: int = 5, window_seconds: int = 60) -> None:
        """Initialize the rate limiter parameters."""
        self.limit = limit
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = {}

    async def __call__(self, request: Request) -> None:
        """Evaluate the request rate and raise an exception if limit exceeded."""
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Filter out timestamps older than the rolling window
        timestamps = self.requests.get(client_ip, [])
        timestamps = [t for t in timestamps if now - t < self.window_seconds]

        if len(timestamps) >= self.limit:
            # Raise custom error mapped to HTTP 403 Forbidden or 429 Too Many Requests
            raise AuthorizationError("Too many authentication attempts. Please try again later.")

        timestamps.append(now)
        self.requests[client_ip] = timestamps


# 5 requests per 60 seconds rolling window
login_rate_limiter = RateLimiter(limit=5, window_seconds=60)
