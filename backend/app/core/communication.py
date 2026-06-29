"""Canonical communication domain object."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.enums.platform import Platform


class CommunicationAttachment(BaseModel):
    """Normalized metadata for a communication attachment."""

    model_config = ConfigDict(extra="forbid")

    name: str
    content_type: str | None = None
    url: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)


class Communication(BaseModel):
    """Normalized message shape produced by every connector."""

    model_config = ConfigDict(extra="forbid")

    platform: Platform
    sender: str
    receiver: str | None = None
    timestamp: datetime
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    attachments: list[CommunicationAttachment] = Field(default_factory=list)
