"""Webhook event schemas."""

from typing import Any, Dict
from pydantic import BaseModel, Field


class WebhookEvent(BaseModel):
    """Encapsulates raw payload and header signature data received from webhook endpoints."""

    platform: str
    headers: Dict[str, str] = Field(default_factory=dict)
    payload: Dict[str, Any] = Field(default_factory=dict)
