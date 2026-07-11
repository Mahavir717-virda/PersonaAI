import pytest
from fastapi.testclient import TestClient

from app.brain.summary.preprocessor import EmailPreprocessor
from app.brain.summary.postprocessor import SummaryPostProcessor
from app.brain.summary.service import LocalSummaryService
from app.main import app

from app.dependencies.auth import get_current_user
from app.models.user import User
import uuid

def mock_get_current_user() -> User:
    return User(
        id=uuid.uuid4(),
        email="test@example.com"
    )

app.dependency_overrides[get_current_user] = mock_get_current_user
client = TestClient(app)


def test_email_preprocessor() -> None:
    """Verify EmailPreprocessor cleans HTML, signatures, and reply headers."""
    raw_email = """
    <p>Hi Sarah,</p>
    Let's review the final slides for Project Atlas today.
    --
    John Smith
    > From: Sarah <sarah@example.com>
    > Let's do it tomorrow instead.
    """
    cleaned = EmailPreprocessor.clean_email_text(raw_email)
    
    assert "Sarah" in cleaned
    assert "Project Atlas" in cleaned
    assert "John Smith" not in cleaned
    assert "sarah@example.com" not in cleaned
    assert "tomorrow" not in cleaned


def test_summary_postprocessor_repair() -> None:
    """Verify SummaryPostProcessor repairs markdown wrappers and missing JSON properties."""
    raw_json = """
    ```json
    {
      "tldr": "Quick status update.",
      "summary": "Reviewing Project Atlas status report details.",
      "action_items": ["Prepare budget presentation"]
    }
    ```
    """
    data = SummaryPostProcessor.clean_and_repair_json(raw_json)
    
    assert data["tldr"] == "Quick status update."
    assert data["summary"] == "Reviewing Project Atlas status report details."
    assert "Prepare budget presentation" in data["action_items"]
    # Missing fields should be populated automatically
    assert isinstance(data["deadlines"], list)
    assert isinstance(data["people"], list)


@pytest.mark.asyncio
async def test_local_summary_service_pipeline() -> None:
    """Verify LocalSummaryService processes text and defaults to fallback payload on mock."""
    service = LocalSummaryService()
    res = await service.generate_structured_summary("Email content regarding Sarah.")
    
    assert res.tldr == "Conversational summary of request context."
    assert "Sarah" in res.people


from unittest.mock import patch, AsyncMock
from app.ai.schemas.summary import SummaryDetail as AISummaryDetail

def test_summary_api_endpoint() -> None:
    """Verify POST /api/v1/summary returns valid structured payload."""
    mock_res = AISummaryDetail(
        tldr="Conversational summary",
        summary="Reviewing Project Atlas status report details.",
        projects=["Project Atlas"]
    )
    with patch("app.api.v1.routes.brain.SummarizerService.summarize_email", AsyncMock(return_value=mock_res)):
        response = client.post(
            "/api/v1/summary",
            json={"conversation": "Email subject Project Atlas."}
        )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Project Atlas" in data["summary"]["projects"]


def test_brain_chat_endpoint() -> None:
    """Verify POST /api/v1/brain/chat routes successfully."""
    mock_res = AISummaryDetail(
        tldr="Conversational summary",
        summary="Meeting scheduled for Sarah",
        people=["Sarah"]
    )
    with patch("app.api.v1.routes.brain.SummarizerService.summarize_email", AsyncMock(return_value=mock_res)):
        response = client.post(
            "/api/v1/brain/chat",
            json={
                "source": "gmail",
                "mode": "summarize",
                "thread": "Meeting scheduled for Sarah on Monday next week."
            }
        )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "summarize" in data["reply"]
    assert "Sarah" in data["summary"]["people"]


def test_model_status_endpoint() -> None:
    """Verify GET /api/v1/models/status returns correct layout status fields."""
    response = client.get("/api/v1/models/status")
    assert response.status_code == 200
    data = response.json()
    assert "loaded" in data
    assert "ready" in data
    assert "device" in data
    assert data["model"] == "PersonaAI Summary V1"

