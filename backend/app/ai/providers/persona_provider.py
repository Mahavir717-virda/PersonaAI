"""Persona AI Provider stub."""

from typing import AsyncGenerator
from app.ai.providers.base import BaseAIProvider

class PersonaProvider(BaseAIProvider):
    """Stub implementation for future custom Persona model integration."""

    async def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        raise NotImplementedError("Persona Provider is not implemented yet.")

    async def stream_chat(self, messages: list[dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        raise NotImplementedError("Persona Provider is not implemented yet.")
        yield ""

    async def embeddings(self, text: str) -> list[float]:
        raise NotImplementedError("Persona Provider is not implemented yet.")

    async def health(self) -> bool:
        return False
