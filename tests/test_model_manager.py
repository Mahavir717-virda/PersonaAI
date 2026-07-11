import pytest
from fastapi.testclient import TestClient

from app.brain.models.summary.loader import SummaryModelLoader
from app.brain.models.manager import AIModelManager
from app.services.summary_service import SummaryService
from app.main import app

client = TestClient(app)


def test_summary_model_loader_singleton() -> None:
    """Verify SummaryModelLoader conforms to Singleton pattern design."""
    loader1 = SummaryModelLoader()
    loader2 = SummaryModelLoader()
    assert loader1 is loader2


def test_model_manager_registration_and_unloading() -> None:
    """Verify registry loading, hot-reload health-checks, and resource unloading."""
    manager = AIModelManager()
    loader = SummaryModelLoader()
    
    manager.register_model("summary_test", "v1", loader)
    manager.load_model("summary_test", "v1")
    assert manager.health_checks()["summary_test:v1"] is True

    # Test unload
    manager.unload_model("summary_test", "v1")
    assert manager.health_checks()["summary_test:v1"] is False


def test_summary_service_inference_structuring() -> None:
    """Verify SummaryService outputs complete structured summary dicts."""
    service = SummaryService()
    res = service.summarize_conversation("Please schedule calendar slot for Sarah next Friday.")
    
    assert "summary" in res
    assert "Sarah" in res["people"]
    assert "Next Friday" in res["deadlines"]
    assert len(res["tasks"]) == 0  # "project" keyword absent from text


def test_inference_api_endpoint() -> None:
    """Verify FastAPI route /api/v1/models/summary returns valid response payloads."""
    response = client.post(
        "/api/v1/models/summary",
        json={"text": "Review project updates next Friday."}
    )
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "Review project proposals" in data["tasks"]
    assert "Next Friday" in data["deadlines"]
