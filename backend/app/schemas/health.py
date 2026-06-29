"""Health check response schemas."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class HealthStatus(BaseModel):
    """Detailed application health payload."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["healthy", "degraded"]
    database: Literal["connected", "unavailable"]
    ollama: Literal["running", "unavailable"]
    version: str
    uptime: str
