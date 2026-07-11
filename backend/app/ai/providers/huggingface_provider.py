"""Hugging Face AI Provider stub."""

from typing import AsyncGenerator
from app.ai.providers.base import BaseAIProvider

class HuggingFaceProvider(BaseAIProvider):
    """Stub implementation for future Hugging Face Integration."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

    async def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        raise NotImplementedError("Hugging Face Provider is not implemented yet.")

    async def stream_chat(self, messages: list[dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        raise NotImplementedError("Hugging Face Provider is not implemented yet.")
        yield ""

    async def embeddings(self, text: str) -> list[float]:
        raise NotImplementedError("Hugging Face Provider is not implemented yet.")

    async def health(self) -> bool:
        return False
