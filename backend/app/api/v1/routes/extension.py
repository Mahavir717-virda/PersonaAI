"""Extension REST API routes."""

from typing import Any, Dict
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.response import ApiResponse

from app.ai.factory import AIProviderFactory
from app.ai.prompts.chat import get_general_chat_prompt

router = APIRouter(prefix="/extension", tags=["Extension API"])


class ChatRequest(BaseModel):
    """Payload to interact with the assistant sidebar."""

    message: str


@router.get(
    "/context",
    response_model=ApiResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Get context metadata",
)
async def get_extension_context(
    current_user: User = Depends(get_current_user),
) -> ApiResponse[Dict[str, Any]]:
    """Return user settings context parameters for extension UI customization."""
    personality = (current_user.settings.ai_personality if current_user.settings else "professional")
    return ApiResponse(
        success=True,
        message="Context retrieved successfully",
        data={
            "ai_personality": personality,
            "sync_interval_minutes": 15,
            "auto_summarize_enabled": True,
        },
    )


@router.post(
    "/chat",
    response_model=ApiResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Interact with extension chat assistant",
)
async def extension_chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
) -> ApiResponse[Dict[str, Any]]:
    """Chat handler for extension sidebar queries calling the configured LLM."""
    try:
        provider = AIProviderFactory.get_provider()
        messages = get_general_chat_prompt(payload.message)
        reply = await provider.chat(messages)
    except Exception as e:
        reply = f"AI Assistant is currently unavailable. (Error: {str(e)})"

    return ApiResponse(
        success=True,
        message="Chat response generated successfully",
        data={
            "reply": reply,
        },
    )
