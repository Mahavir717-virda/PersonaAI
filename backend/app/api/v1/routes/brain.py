"""Exposes endpoints for the local summary model and unified Brain router."""

from __future__ import annotations

from typing import Dict, Any, List
from fastapi import APIRouter, status, HTTPException, Depends
from pydantic import BaseModel, Field

from app.dependencies.auth import get_current_user
from app.models.user import User
from app.brain.summary.schemas import SummaryDetail, SummaryResponse
from app.ai.services.summarizer_service import SummarizerService
from app.brain.schemas.state import BrainState, AIMessage, MessageRole
from app.brain.orchestrator.dependencies import BrainContainer
from app.brain.orchestrator.executor import GraphExecutor, CheckpointService
from app.brain.orchestrator.graph import build_brain_graph

router = APIRouter(tags=["Brain API"])


class BrainChatRequest(BaseModel):
    """Payload to route chat queries to the LangGraph brain runtime."""
    source: str = Field(default="gmail", description="Communication source (e.g. gmail).")
    mode: str = Field(default="summarize", description="Action execution mode (e.g. summarize).")
    thread: str = Field(..., description="Email thread text content.")


class BrainChatResponse(BaseModel):
    """Unified API response for brain chat route."""
    success: bool
    reply: str
    summary: SummaryDetail


@router.post(
    "/summary",
    response_model=SummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get structured conversation summary",
)
async def generate_summary(
    payload: dict,
    current_user: User = Depends(get_current_user),
) -> SummaryResponse:
    """Endpoint serving structured summaries using local Summary Model V1."""
    text = payload.get("conversation", "")
    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'conversation' field in payload."
        )
    try:
        service = SummarizerService()
        ai_res = await service.summarize_email(text)
        res = SummaryDetail(**ai_res.model_dump())
        return SummaryResponse(success=True, summary=res)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summary generation failed: {str(e)}"
        )


@router.post(
    "/brain/chat",
    response_model=BrainChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Route query to LangGraph runtime",
)
async def brain_chat(
    payload: BrainChatRequest,
    current_user: User = Depends(get_current_user),
) -> BrainChatResponse:
    """Unified endpoint routing thread content through LangGraph engines."""
    try:
        # 1. Initialize State with user SNAPSHOT context
        from app.brain.schemas.state import BrainContext, UserProfileSnapshot
        from uuid import uuid4
        profile = UserProfileSnapshot(
            user_id=current_user.id,
            timezone="UTC",
            language="en",
            permissions=["read"]
        )
        context = BrainContext(
            session_id=uuid4(),
            tenant_id="default-tenant",
            user_profile=profile
        )
        state = BrainState(context=context)

        # 2. Inject incoming message content
        incoming = AIMessage(
            role=MessageRole.USER,
            sender="user",
            recipient="ai",
            content=payload.thread
        )
        state = state.update(conversation=state.conversation.model_copy(update={
            "incoming_message": incoming
        }))

        # 3. Setup LangGraph runtime executor
        container = BrainContainer()
        compiled_graph = build_brain_graph(container)
        checkpoint_service = CheckpointService(memory_saver=None)
        executor = GraphExecutor(compiled_graph=compiled_graph, checkpoint_service=checkpoint_service)

        # 4. Run StateGraph execution
        final_state = await executor.execute_run(state, thread_id=str(uuid4()))

        # 5. Extract structured summary from SummarizerService
        service = SummarizerService()
        ai_res = await service.summarize_email(payload.thread)
        summary_res = SummaryDetail(**ai_res.model_dump())

        reply_msg = f"Brain processed thread successfully in '{payload.mode}' mode."
        return BrainChatResponse(
            success=True,
            reply=reply_msg,
            summary=summary_res
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Brain execution failure: {str(e)}"
        )
