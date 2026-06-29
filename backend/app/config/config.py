"""Settings access helpers."""

from functools import lru_cache

from app.config.settings import Settings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings loaded from the environment."""
    return Settings()
