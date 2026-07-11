"""AI schema response models."""

from pydantic import BaseModel, Field

class TokenUsage(BaseModel):
    """Token usage metrics for the generation request."""
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None

class ChatResponse(BaseModel):
    """Unified response containing final completion and execution metadata."""
    content: str = Field(..., description="The generated message content")
    model: str = Field(..., description="The name of the model that served the request")
    usage: TokenUsage | None = Field(None, description="Metadata containing token usage")
