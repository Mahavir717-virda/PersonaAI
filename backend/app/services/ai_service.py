"""AI Service for local inference pipeline using LangChain ChatOllama."""

import logging
from typing import Any

from langchain_ollama import ChatOllama

from app.config.config import get_settings

logger = logging.getLogger(__name__)


class AIService:
    """Production-grade AI Service to run local model inference using LangChain."""

    def __init__(self) -> None:
        settings = get_settings()
        logger.info(
            "Initializing ChatOllama with base_url=%s, model=%s",
            settings.ollama_base_url,
            settings.ollama_model,
        )
        self.llm = ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=0.3,
        )

    def ask(self, prompt: str) -> str:
        """Synchronously query the LLM model."""
        try:
            logger.debug("Executing sync query to LLM: %s", prompt[:100])
            response = self.llm.invoke(prompt)
            # LangChain's response content is typed as str or Union, typically str for chat
            content = response.content
            if isinstance(content, bytes):
                return content.decode("utf-8")
            return str(content)
        except Exception as e:
            logger.error("Error in sync LLM invocation: %s", e, exc_info=True)
            raise RuntimeError(f"Local AI inference failed: {str(e)}") from e

    async def ask_async(self, prompt: str) -> str:
        """Asynchronously query the LLM model (recommended for FastAPI)."""
        try:
            logger.debug("Executing async query to LLM: %s", prompt[:100])
            response = await self.llm.ainvoke(prompt)
            content = response.content
            if isinstance(content, bytes):
                return content.decode("utf-8")
            return str(content)
        except Exception as e:
            logger.error("Error in async LLM invocation: %s", e, exc_info=True)
            raise RuntimeError(f"Local AI inference failed: {str(e)}") from e
