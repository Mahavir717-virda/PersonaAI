"""Summarizer service."""

import json
from app.ai.factory import AIProviderFactory
from app.ai.prompts.summarize import get_summarize_prompt
from app.ai.schemas.summary import SummaryDetail

class SummarizerService:
    """Orchestrates summarization logic using the configured AI provider."""

    def __init__(self, provider_name: str | None = None) -> None:
        self.provider = AIProviderFactory.get_provider(provider_name)

    async def summarize_email(self, text: str) -> SummaryDetail:
        """Generates a structured email summary from raw conversation text."""
        messages = get_summarize_prompt(text)
        raw_response = await self.provider.chat(messages)
        
        parsed_data = self._clean_and_parse_json(raw_response)
        return SummaryDetail(**parsed_data)

    def _clean_and_parse_json(self, raw: str) -> dict:
        """Utility to safely extract and parse JSON from LLM response."""
        cleaned = raw.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {
                "tldr": "Failed to parse structured summary.",
                "summary": cleaned,
                "key_points": [],
                "decisions": [],
                "action_items": [],
                "deadlines": [],
                "people": [],
                "organizations": [],
                "projects": [],
                "meetings": [],
                "risks": [],
                "follow_ups": [],
                "questions": [],
                "topics": []
            }
