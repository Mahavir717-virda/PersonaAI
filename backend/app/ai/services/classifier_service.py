"""Message classification service."""

from app.ai.factory import AIProviderFactory

class ClassifierService:
    """Orchestrates email/message classification."""

    def __init__(self, provider_name: str | None = None) -> None:
        self.provider = AIProviderFactory.get_provider(provider_name)

    async def classify_message(self, text: str) -> dict[str, str]:
        """Classifies sentiment, priority, and category of a message."""
        prompt = (
            "You are PersonaAI. Classify the following email content.\n"
            "Return a JSON object with exactly these fields:\n"
            "- 'priority': 'HIGH', 'MEDIUM', or 'LOW'\n"
            "- 'category': 'WORK', 'PERSONAL', 'SOCIAL', 'FINANCIAL', or 'SPAM'\n"
            "- 'sentiment': 'POSITIVE', 'NEGATIVE', or 'NEUTRAL'\n\n"
            "Do not include markdown headers or other characters outside the JSON payload."
        )
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ]
        response = await self.provider.chat(messages)
        return self._parse_classification(response)

    def _parse_classification(self, raw: str) -> dict[str, str]:
        import json
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
                "priority": "MEDIUM",
                "category": "WORK",
                "sentiment": "NEUTRAL"
            }
