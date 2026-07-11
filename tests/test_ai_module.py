import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import groq

from app.config import get_settings
from app.ai.factory import AIProviderFactory
from app.ai.providers.groq_provider import GroqProvider
from app.ai.providers.ollama_provider import OllamaProvider
from app.ai.exceptions.provider_exception import (
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderAPIError,
)
from app.ai.services.summarizer_service import SummarizerService
from app.ai.services.task_service import TaskService
from app.ai.services.reply_service import ReplyService
from app.ai.services.classifier_service import ClassifierService

def test_factory_returns_correct_provider() -> None:
    """Verify that factory resolves active provider name correctly."""
    settings = get_settings()
    
    with patch.object(settings, "ai_provider", "groq"):
        with patch.object(settings, "groq_api_key", "test_key"):
            provider = AIProviderFactory.get_provider()
            assert isinstance(provider, GroqProvider)

    with patch.object(settings, "ai_provider", "ollama"):
        provider = AIProviderFactory.get_provider()
        assert isinstance(provider, OllamaProvider)


def test_factory_invalid_provider_raises_error() -> None:
    """Verify that invalid provider names raise exceptions."""
    settings = get_settings()
    with patch.object(settings, "ai_provider", "unsupported_llm"):
        with pytest.raises(Exception) as excinfo:
            AIProviderFactory.get_provider()
        assert "Unsupported AI provider" in str(excinfo.value)


def test_groq_provider_missing_key_raises_auth_error() -> None:
    """Verify that constructing GroqProvider without a key fails gracefully."""
    with pytest.raises(ProviderAuthenticationError):
        GroqProvider(api_key=None)
    with pytest.raises(ProviderAuthenticationError):
        GroqProvider(api_key="  ")
    with pytest.raises(ProviderAuthenticationError):
        GroqProvider(api_key="Your_API_Key")


@pytest.mark.asyncio
async def test_groq_provider_exception_mapping() -> None:
    """Verify that Groq SDK exceptions map correctly to custom exceptions."""
    provider = GroqProvider(api_key="mock_key")
    
    # Mocking standard Groq exception flows
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"

    # Authenticate error mapping
    with patch.object(provider.client.chat.completions, "create", AsyncMock(side_effect=groq.AuthenticationError("Invalid API key", response=mock_response, body=None))):
        with pytest.raises(ProviderAuthenticationError):
            await provider.chat([{"role": "user", "content": "hi"}])

    # Rate limit error mapping
    mock_response.status_code = 429
    with patch.object(provider.client.chat.completions, "create", AsyncMock(side_effect=groq.RateLimitError("Rate limit exceeded", response=mock_response, body=None))):
        with pytest.raises(ProviderRateLimitError):
            await provider.chat([{"role": "user", "content": "hi"}])

    # Timeout error mapping
    with patch.object(provider.client.chat.completions, "create", AsyncMock(side_effect=groq.APITimeoutError("Request timed out"))):
        with pytest.raises(ProviderTimeoutError):
            await provider.chat([{"role": "user", "content": "hi"}])


@pytest.mark.asyncio
async def test_groq_chat_completion_success() -> None:
    """Verify successful chat completion returns content."""
    provider = GroqProvider(api_key="mock_key")
    
    mock_chat_completion = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "Hello there!"
    mock_choice.message = mock_message
    mock_chat_completion.choices = [mock_choice]
    
    with patch.object(provider.client.chat.completions, "create", AsyncMock(return_value=mock_chat_completion)) as mock_create:
        res = await provider.chat([{"role": "user", "content": "hi"}])
        assert res == "Hello there!"
        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_groq_streaming_completion() -> None:
    """Verify that stream_chat yields increments correctly."""
    provider = GroqProvider(api_key="mock_key")
    
    # Setup mock stream iterator
    async def mock_stream_iter():
        chunks = ["Hello", " ", "world", "!"]
        for chunk in chunks:
            mock_chunk = MagicMock()
            mock_delta = MagicMock()
            mock_delta.content = chunk
            mock_choice = MagicMock()
            mock_choice.delta = mock_delta
            mock_chunk.choices = [mock_choice]
            yield mock_chunk

    with patch.object(provider.client.chat.completions, "create", AsyncMock(return_value=mock_stream_iter())) as mock_create:
        output_chunks = []
        async for chunk in provider.stream_chat([{"role": "user", "content": "hi"}]):
            output_chunks.append(chunk)
        
        assert "".join(output_chunks) == "Hello world!"


@pytest.mark.asyncio
async def test_services_call_underlying_providers() -> None:
    """Verify high-level services leverage provider chat correctly."""
    mock_provider = AsyncMock()
    # Mocking standard structured JSON response for summarizer
    mock_provider.chat.return_value = """
    {
      "tldr": "Project update",
      "summary": "Reviewing budget details",
      "action_items": ["Prepare budget presentation"]
    }
    """
    
    with patch("app.ai.factory.AIProviderFactory.get_provider", return_value=mock_provider):
        service = SummarizerService()
        res = await service.summarize_email("Draft budget email details.")
        assert res.tldr == "Project update"
        assert "Prepare budget presentation" in res.action_items
        mock_provider.chat.assert_called_once()

    # Test TaskService
    mock_provider.chat.reset_mock()
    mock_provider.chat.return_value = '{"tasks": ["Submit deliverables report"]}'
    with patch("app.ai.factory.AIProviderFactory.get_provider", return_value=mock_provider):
        task_service = TaskService()
        tasks = await task_service.extract_tasks("Submit by Monday.")
        assert tasks == ["Submit deliverables report"]

    # Test ReplyService
    mock_provider.chat.reset_mock()
    mock_provider.chat.return_value = "Sure, I will be there."
    with patch("app.ai.factory.AIProviderFactory.get_provider", return_value=mock_provider):
        reply_service = ReplyService()
        reply = await reply_service.generate_reply("Are you coming?", tone="casual")
        assert reply == "Sure, I will be there."

    # Test ClassifierService
    mock_provider.chat.reset_mock()
    mock_provider.chat.return_value = '{"priority": "HIGH", "category": "WORK", "sentiment": "POSITIVE"}'
    with patch("app.ai.factory.AIProviderFactory.get_provider", return_value=mock_provider):
        classifier_service = ClassifierService()
        classification = await classifier_service.classify_message("This is highly urgent project task.")
        assert classification["priority"] == "HIGH"
        assert classification["category"] == "WORK"
