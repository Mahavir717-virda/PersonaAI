"""Smart reply generation service."""

from app.ai.factory import AIProviderFactory
from app.ai.prompts.reply import get_reply_prompt

class ReplyService:
    """Orchestrates generating responses to emails/messages."""

    def __init__(self, provider_name: str | None = None) -> None:
        self.provider = AIProviderFactory.get_provider(provider_name)

    async def generate_reply(self, original_text: str, tone: str = "professional") -> str:
        """Generates a reply draft to an email using the configured provider."""
        messages = get_reply_prompt(original_text, tone)
        return await self.provider.chat(messages)
