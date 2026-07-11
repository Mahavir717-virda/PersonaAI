"""Task service."""

import json
from app.ai.factory import AIProviderFactory
from app.ai.prompts.task import get_task_extraction_prompt

class TaskService:
    """Orchestrates task extraction from text."""

    def __init__(self, provider_name: str | None = None) -> None:
        self.provider = AIProviderFactory.get_provider(provider_name)

    async def extract_tasks(self, text: str) -> list[str]:
        """Extracts actionable tasks from text using configured provider."""
        messages = get_task_extraction_prompt(text)
        raw_response = await self.provider.chat(messages)
        return self._parse_tasks(raw_response)

    def _parse_tasks(self, raw: str) -> list[str]:
        cleaned = raw.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
            if isinstance(data, dict) and "tasks" in data:
                return data["tasks"]
            elif isinstance(data, list):
                return data
            return []
        except json.JSONDecodeError:
            return [line.strip("- *").strip() for line in cleaned.splitlines() if line.strip()]
