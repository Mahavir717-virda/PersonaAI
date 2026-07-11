"""AI schema request models."""

from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    """A single chat message in a conversation sequence."""
    role: str = Field(..., description="Role of the sender: 'system', 'user', or 'assistant'")
    content: str = Field(..., description="The string content of the message")

class ChatRequest(BaseModel):
    """Payload to request chat completion from an AI provider."""
    messages: list[ChatMessage] = Field(..., description="Chronological sequence of chat history")
    temperature: float | None = Field(None, description="Sampling temperature")
    max_tokens: int | None = Field(None, description="Max tokens to generate")
    stream: bool = Field(default=False, description="Whether to stream response chunks")
