"""Base AI Provider interface."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator

class BaseAIProvider(ABC):
    """Abstract interface enforcing standardized interactions with all LLM engines."""

    @abstractmethod
    async def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        """Executes a blocking chat completion request."""
        pass

    @abstractmethod
    async def stream_chat(self, messages: list[dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """Executes a streaming chat completion request yielding incremental string chunks."""
        yield ""

    @abstractmethod
    async def embeddings(self, text: str) -> list[float]:
        """Generates vector embeddings for a given input text."""
        pass

    @abstractmethod
    async def health(self) -> bool:
        """Performs a status ping to check if the underlying provider API is reachable."""
        pass
