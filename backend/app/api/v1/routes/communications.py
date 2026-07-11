"""Communication REST API routes."""

from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, status, Path, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.communication import CommunicationService
from app.schemas.response import ApiResponse

router = APIRouter(tags=["Communications"])


class AttachmentResponse(BaseModel):
    """File attachment summary."""

    id: str
    name: str
    content_type: str | None
    url: str | None
    size_bytes: int | None


class CommunicationDetailResponse(BaseModel):
    """Normalized communication metadata."""

    id: str
    platform: str
    platform_message_id: str
    subject: str | None
    body: str
    html_body: str | None
    status: str
    importance: str
    created_at: str
    sender_name: str
    sender_address: str
    receivers: List[str]
    attachments: List[AttachmentResponse]
    metadata: Dict[str, Any]


class ConversationResponse(BaseModel):
    """Normalized message thread/conversation record."""

    id: str
    platform: str
    platform_conversation_id: str
    created_at: str


@router.get(
    "/communications",
    response_model=ApiResponse[List[CommunicationDetailResponse]],
    status_code=status.HTTP_200_OK,
    summary="List normalized communications",
)
async def list_communications(
    platform: Optional[str] = Query(
        None, description="Filter by platform (gmail, whatsapp)"
    ),
    status_str: Optional[str] = Query(
        None, alias="status", description="Filter by read status"
    ),
    exclude_query: Optional[str] = Query(
        None,
        description="Exclude messages whose subject/body/sender contains this pattern",
    ),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[List[CommunicationDetailResponse]]:
    """Return a paginated list of normalized communications received by the user."""
    service = CommunicationService(session)
    records = await service.list_communications(
        user_id=current_user.id,
        platform_str=platform,
        status_str=status_str,
        exclude_query=exclude_query,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(
        success=True,
        message="Communications retrieved successfully",
        data=[CommunicationDetailResponse(**r) for r in records],
    )


@router.get(
    "/communications/search",
    response_model=ApiResponse[List[CommunicationDetailResponse]],
    status_code=status.HTTP_200_OK,
    summary="Search communications",
)
async def search_communications(
    query: Optional[str] = Query(
        None, description="Keywords search on body, subject, or participants"
    ),
    platform: Optional[str] = Query(
        None, description="Filter by platform (gmail, whatsapp)"
    ),
    sender: Optional[str] = Query(None, description="Filter by sender address or name"),
    subject: Optional[str] = Query(None, description="Filter by subject keyword"),
    exclude_query: Optional[str] = Query(
        None,
        description="Exclude messages whose subject/body/sender contains this pattern",
    ),
    start_date: Optional[datetime] = Query(
        None, description="Filter by start date threshold"
    ),
    end_date: Optional[datetime] = Query(
        None, description="Filter by end date threshold"
    ),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[List[CommunicationDetailResponse]]:
    """Search communications using keywords, dates, subjects, or sender identity."""
    service = CommunicationService(session)
    records = await service.search_communications(
        user_id=current_user.id,
        query=query,
        platform_str=platform,
        sender=sender,
        subject=subject,
        exclude_query=exclude_query,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(
        success=True,
        message="Search completed successfully",
        data=[CommunicationDetailResponse(**r) for r in records],
    )


@router.get(
    "/communications/recent",
    response_model=ApiResponse[List[CommunicationDetailResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get recent communications",
)
async def get_recent_communications(
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[List[CommunicationDetailResponse]]:
    """Retrieve the most recent communications for inbox feeds."""
    service = CommunicationService(session)
    records = await service.get_recent(user_id=current_user.id, limit=limit)
    return ApiResponse(
        success=True,
        message="Recent communications retrieved successfully",
        data=[CommunicationDetailResponse(**r) for r in records],
    )


@router.get(
    "/communications/summary",
    response_model=ApiResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Get communication summary stats",
)
async def get_communication_summary(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[Dict[str, Any]]:
    """Return communication metrics per platform."""
    service = CommunicationService(session)
    summary = await service.get_summary(current_user.id)
    return ApiResponse(
        success=True,
        message="Summary stats retrieved successfully",
        data=summary,
    )


@router.get(
    "/communications/{id}",
    response_model=ApiResponse[CommunicationDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Get communication details",
)
async def get_communication_detail(
    communication_id: uuid.UUID = Path(
        ..., alias="id", description="Communication UUID"
    ),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[CommunicationDetailResponse]:
    """Fetch communication metadata by ID."""
    service = CommunicationService(session)
    try:
        record = await service.get_communication_detail(
            user_id=current_user.id, communication_id=communication_id
        )
    except PermissionError as e:
        return ApiResponse(success=False, message=str(e), data=None)  # type: ignore

    if not record:
        return ApiResponse(success=False, message="Communication not found", data=None)  # type: ignore

    return ApiResponse(
        success=True,
        message="Communication details retrieved successfully",
        data=CommunicationDetailResponse(**record),
    )


@router.get(
    "/conversations",
    response_model=ApiResponse[List[ConversationResponse]],
    status_code=status.HTTP_200_OK,
    summary="List conversations/threads",
)
async def list_conversations(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[List[ConversationResponse]]:
    """Return paginated list of conversations/threads involving user communications."""
    service = CommunicationService(session)
    records = await service._repo.list_conversations(
        user_id=current_user.id, limit=limit, offset=offset
    )
    data_list = [
        ConversationResponse(
            id=str(c.id),
            platform=c.platform.name.lower(),
            platform_conversation_id=c.platform_conversation_id,
            created_at=c.created_at.isoformat(),
        )
        for c in records
    ]
    return ApiResponse(
        success=True,
        message="Conversations retrieved successfully",
        data=data_list,
    )
