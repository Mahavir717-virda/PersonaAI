"""Routes for the local model deployment and inference pipeline."""

from fastapi import APIRouter, status, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List

from app.services.summary_service import SummaryService

router = APIRouter(tags=["Models"])


class SummaryInferenceRequest(BaseModel):
    """Payload containing input text to summarize."""
    text: str = Field(..., description="Conversational text to analyze.")
    version: str | None = Field(default=None, description="Model version override.")


class SummaryInferenceResponse(BaseModel):
    """Payload containing structured summary segments."""
    summary: str
    tasks: List[str]
    people: List[str]
    deadlines: List[str]


@router.post(
    "/models/summary",
    response_model=SummaryInferenceResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a structured summary using local model",
)
async def generate_summary(payload: SummaryInferenceRequest) -> SummaryInferenceResponse:
    """Invokes local model to generate structured JSON summary outputs."""
    try:
        service = SummaryService()
        result = service.summarize_conversation(payload.text, payload.version)
        return SummaryInferenceResponse(
            summary=result.get("summary", ""),
            tasks=result.get("tasks", []),
            people=result.get("people", []),
            deadlines=result.get("deadlines", []),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error: {str(e)}"
        )


@router.get(
    "/models/status",
    status_code=status.HTTP_200_OK,
    summary="Get status of local Summary Model V1",
)
async def get_model_status() -> Dict[str, Any]:
    """Check whether local Summary Model V1 is loaded and ready in memory."""
    from app.brain.summary.loader import SummaryModelLoader
    loader = SummaryModelLoader()
    is_ready = loader.health_check()
    
    device_str = "cpu"
    if is_ready and loader.model:
        try:
            # Check if PyTorch device is available
            device_str = str(loader.model.device)
        except Exception:
            pass

    return {
        "loaded": is_ready,
        "ready": is_ready,
        "device": device_str,
        "model": "PersonaAI Summary V1",
        "version": "1.0.0"
    }

