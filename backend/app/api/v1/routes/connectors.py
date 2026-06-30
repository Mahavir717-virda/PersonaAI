"""Connector REST API routes."""

import logging
import uuid
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query, status, Path
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.database.session import get_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.repositories.connector import ConnectorRepository
from app.services.communication import CommunicationService
from app.services.credential_manager import CredentialManager
from app.services.connector import ConnectorService
from app.services.pipeline import CommunicationPipeline
from app.services.sync import SyncService
from app.schemas.response import ApiResponse
from app.enums.platform import Platform
from app.enums.connector_state import ConnectorState
from app.connectors import connector_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/connectors", tags=["Connectors"])


class ConnectRequest(BaseModel):
    """Payload to authorize and configure a platform integration."""

    auth_data: Dict[str, Any]


class ConnectResponse(BaseModel):
    """Outcome metadata of the connect request."""

    id: str
    platform: str
    state: str


class SyncResultResponse(BaseModel):
    """Synchronization outcome metrics."""

    status: str
    messages_imported: int
    attachments_imported: int
    error: str | None


class MetricsResponse(BaseModel):
    """Aggregated usage metrics."""

    connected_accounts: int
    total_syncs: int
    failed_syncs: int
    messages_imported: int
    avg_sync_time_seconds: float


class GmailAttachmentResponse(BaseModel):
    """Attachment metadata for Gmail inbox payloads."""

    id: str
    name: str
    content_type: str | None
    size_bytes: int | None


class GmailMessageResponse(BaseModel):
    """Normalized Gmail message payload returned to the inbox UI."""

    id: str
    communication_id: str
    platform_message_id: str
    thread_id: str | None
    subject: str | None
    body: str
    sender_name: str
    sender_address: str
    recipient_address: str
    attachments: List[GmailAttachmentResponse]
    created_at: str
    labels: List[str]
    snippet: str | None
    unread: bool


class GmailMessagesResponse(BaseModel):
    """Batch of Gmail messages returned with the next cursor."""

    messages: List[GmailMessageResponse]
    next_cursor: str | None


@router.get(
    "",
    response_model=ApiResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="List connectors and available platforms",
)
async def list_connectors(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[Dict[str, Any]]:
    """Return configured user connectors along with the registry of all available connectors."""
    service = ConnectorService(session)
    active = await service.list_user_connectors(current_user.id)
    available = await service.list_available_connectors()
    return ApiResponse(
        success=True,
        message="Connectors listed successfully",
        data={"active": active, "available": available},
    )


@router.get(
    "/metrics",
    response_model=ApiResponse[MetricsResponse],
    status_code=status.HTTP_200_OK,
    summary="Get aggregated connector metrics",
)
async def get_connector_metrics(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[MetricsResponse]:
    """Retrieve counts of sync iterations, imported messages, and error states."""
    service = ConnectorService(session)
    metrics = await service.get_metrics(current_user.id)
    return ApiResponse(
        success=True,
        message="Metrics retrieved successfully",
        data=MetricsResponse(**metrics),
    )


def _serialize_gmail_message(raw_record: dict[str, Any], communication: Any) -> GmailMessageResponse:
    """Serialize a normalized Gmail communication for the inbox UI."""
    metadata = communication.metadata_fields or {}
    sender = next((participant for participant in communication.participants if participant.type == "sender"), None)
    recipient = next((participant for participant in communication.participants if participant.type == "recipient"), None)

    return GmailMessageResponse(
        id=raw_record["id"],
        communication_id=str(communication.id),
        platform_message_id=communication.platform_message_id,
        thread_id=(metadata.get("thread_id") or raw_record.get("thread_id")),
        subject=communication.subject,
        body=communication.body,
        sender_name=sender.name if sender and sender.name else "Unknown",
        sender_address=sender.address if sender else "",
        recipient_address=recipient.address if recipient else raw_record.get("recipient_address", ""),
        attachments=[
            GmailAttachmentResponse(
                id=str(attachment.id),
                name=attachment.name,
                content_type=attachment.content_type,
                size_bytes=attachment.size_bytes,
            )
            for attachment in communication.attachments
        ],
        created_at=communication.created_at.isoformat(),
        labels=list(metadata.get("labels") or raw_record.get("labels") or []),
        snippet=metadata.get("snippet") or raw_record.get("snippet"),
        unread=bool(metadata.get("unread", raw_record.get("unread", False))),
    )


def _serialize_stored_gmail_message(message: dict[str, Any]) -> GmailMessageResponse:
    """Serialize an already-persisted Gmail communication for the inbox UI."""
    metadata = message.get("metadata") or {}
    attachments = [
        GmailAttachmentResponse(
            id=attachment["id"],
            name=attachment["name"],
            content_type=attachment.get("content_type"),
            size_bytes=attachment.get("size_bytes"),
        )
        for attachment in message.get("attachments", [])
    ]
    return GmailMessageResponse(
        id=message["id"],
        communication_id=message["id"],
        platform_message_id=message["platform_message_id"],
        thread_id=metadata.get("thread_id"),
        subject=message.get("subject"),
        body=message.get("body", ""),
        sender_name=message.get("sender_name", "Unknown"),
        sender_address=message.get("sender_address", ""),
        recipient_address=(message.get("receivers") or [""])[0],
        attachments=attachments,
        created_at=message.get("created_at", ""),
        labels=list(metadata.get("labels") or []),
        snippet=metadata.get("snippet"),
        unread=bool(metadata.get("unread", False)),
    )



@router.post(
    "/{platform}/connect",
    response_model=ApiResponse[ConnectResponse],
    status_code=status.HTTP_200_OK,
    summary="Connect a platform integration",
)
async def connect_platform(
    payload: ConnectRequest,
    platform: str = Path(..., description="The platform key (e.g. gmail, whatsapp)"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[ConnectResponse]:
    """Initialize credentials and activate a platform connector."""
    service = ConnectorService(session)
    res = await service.connect_platform(
        user_id=current_user.id, platform_str=platform, auth_data=payload.auth_data
    )
    return ApiResponse(
        success=True,
        message=f"{platform.capitalize()} integration connected successfully",
        data=ConnectResponse(**res),
    )


@router.post(
    "/{platform}/disconnect",
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Disconnect a platform integration",
)
async def disconnect_platform(
    platform: str = Path(..., description="The platform key (e.g. gmail, whatsapp)"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[None]:
    """Revoke active credentials and remove a platform integration from the workspace."""
    service = ConnectorService(session)
    await service.disconnect_platform(user_id=current_user.id, platform_str=platform)
    return ApiResponse(
        success=True,
        message=f"{platform.capitalize()} integration disconnected successfully",
        data=None,
    )


@router.post(
    "/{platform}/sync",
    response_model=ApiResponse[SyncResultResponse],
    status_code=status.HTTP_200_OK,
    summary="Trigger a manual sync loop",
)
async def sync_platform(
    platform: str = Path(..., description="The platform key (e.g. gmail, whatsapp)"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[SyncResultResponse]:
    """Manually invoke the synchronization loop to pull message lists from the provider."""
    sync_service = SyncService(session)
    res = await sync_service.trigger_sync(user_id=current_user.id, platform_str=platform)
    return ApiResponse(
        success=True,
        message=f"{platform.capitalize()} sync finished",
        data=SyncResultResponse(**res),
    )


@router.get(
    "/{platform}/messages",
    response_model=ApiResponse[GmailMessagesResponse],
    status_code=status.HTTP_200_OK,
    summary="List Gmail inbox messages",
)
async def list_platform_messages(
    platform: str = Path(..., description="The platform key (currently gmail)"),
    refresh: bool = Query(False, description="Refresh the inbox before reading stored messages"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[GmailMessagesResponse]:
    """Return stored Gmail messages for the inbox view, optionally refreshing first."""
    if platform.lower() != "gmail":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message listing is only implemented for Gmail",
        )

    if refresh:
        sync_service = SyncService(session)
        sync_result = await sync_service.trigger_sync(user_id=current_user.id, platform_str=platform)
        if sync_result.get("status") == "failed":
            logger.warning(
                "Gmail refresh failed for user %s: %s",
                current_user.id,
                sync_result.get("error"),
            )

    service = CommunicationService(session)
    records = await service.list_communications(
        user_id=current_user.id,
        platform_str=platform,
        limit=100,
        offset=0,
    )
    messages = [_serialize_stored_gmail_message(record) for record in records]
    return ApiResponse(
        success=True,
        message="Gmail messages retrieved successfully",
        data=GmailMessagesResponse(messages=messages, next_cursor=None),
    )


@router.get(
    "/{platform}/health",
    response_model=ApiResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Check platform health",
)
async def check_platform_health(
    platform: str = Path(..., description="The platform key (e.g. gmail, whatsapp)"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[Dict[str, Any]]:
    """Query external platform services to verify token and scope validity."""
    service = ConnectorService(session)
    is_healthy = await service.check_health(user_id=current_user.id, platform_str=platform)
    return ApiResponse(
        success=True,
        message=f"{platform.capitalize()} health status checked",
        data={"healthy": is_healthy},
    )
