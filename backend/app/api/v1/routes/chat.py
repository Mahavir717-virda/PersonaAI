"""FastAPI router for AI Chat endpoints using local LLMs."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.services.ai_service import AIService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat"])


class ChatRequest(BaseModel):
    """Request schema for the AI Chat endpoint."""
    prompt: str = Field(..., description="The query or message to send to the local AI model.")


class ChatResponse(BaseModel):
    """Response schema for the AI Chat endpoint."""
    response: str = Field(..., description="The content returned by the local AI model.")


def get_ai_service() -> AIService:
    """Dependency to retrieve the AI service instance."""
    return AIService()


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a prompt to the local AI model",
)
async def chat(
    request: ChatRequest,
    ai_service: AIService = Depends(get_ai_service),
) -> ChatResponse:
    """Invokes the local Ollama Llama 3.2 model using LangChain.

    Flow:
    React Frontend -> FastAPI (/chat) -> AIService -> LangChain ChatOllama -> Ollama (Llama 3.2) -> Response
    """
    try:
        response_text = await ai_service.ask_async(request.prompt)
        return ChatResponse(response=response_text)
    except Exception as e:
        logger.error("Failed to complete chat generation: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI inference service is currently unavailable: {str(e)}",
        )
