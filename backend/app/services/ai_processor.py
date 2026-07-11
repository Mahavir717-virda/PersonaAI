"""AI processor interface definition."""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class AIProcessor:
    """Interface declaring Ollama and OpenAI model generation tasks."""

    async def summarize(self, text: str) -> str:
        """Generate summary for the given text."""
        logger.info("[AIProcessor] Generating mock summary...")
        return "Sarah requested roadmap updates."

    async def extract_tasks(self, text: str) -> List[Dict[str, Any]]:
        """Extract task cards from message text."""
        logger.info("[AIProcessor] Extracting mock tasks...")
        return [{"title": "Review Q3 Roadmap", "due": "Friday"}]

    async def classify_priority(self, text: str) -> str:
        """Assess priority importance tags (high, medium, low)."""
        logger.info("[AIProcessor] Classifying priority...")
        return "high" if "urgent" in text.lower() or "asap" in text.lower() else "medium"

    async def generate_reply(self, context: str, tone: str = "professional") -> str:
        """Create draft reply suggestions."""
        logger.info("[AIProcessor] Drafting mock reply...")
        return "Thanks, I will take a look."
