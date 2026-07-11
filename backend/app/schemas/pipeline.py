"""Schemas for the communication processing pipeline."""

import uuid
from pydantic import BaseModel


class ProcessPayloadResult(BaseModel):
    """Result of processing a single payload in the communication pipeline."""

    communication_id: uuid.UUID
    attachment_count: int
    is_new: bool
