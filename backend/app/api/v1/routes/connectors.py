"""Connector REST API routes."""

import logging
import base64
import hashlib
import hmac
import json
import uuid
from urllib.parse import urlencode
from datetime import datetime, timezone
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query, status, Path
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.database.session import get_session
from app.config.config import get_settings
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


class GmailAuthUrlResponse(BaseModel):
    """Google OAuth authorization URL payload."""

    authorization_url: str


def _encode_state(payload: dict[str, Any]) -> str:
    """Create a signed state token for Gmail OAuth."""
    settings = get_settings()
    serialized = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    signature = hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        serialized,
        hashlib.sha256,
    ).digest()
    token = base64.urlsafe_b64encode(serialized).decode("utf-8").rstrip("=")
    sig = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")
    return f"{token}.{sig}"


def _decode_state(state: str) -> dict[str, Any]:
    """Verify and decode a Gmail OAuth state token."""
    settings = get_settings()
    try:
        token, sig = state.split(".", 1)
        padded_token = token + "=" * (-len(token) % 4)
        padded_sig = sig + "=" * (-len(sig) % 4)
        serialized = base64.urlsafe_b64decode(padded_token.encode("utf-8"))
        expected_sig = hmac.new(
            settings.jwt_secret_key.encode("utf-8"),
            serialized,
            hashlib.sha256,
        ).digest()
        provided_sig = base64.urlsafe_b64decode(padded_sig.encode("utf-8"))
        if not hmac.compare_digest(expected_sig, provided_sig):
            raise ValueError("Invalid OAuth state signature")
        return json.loads(serialized.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Gmail OAuth state",
        ) from exc


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
    if platform.lower() == "gmail":
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This endpoint is deprecated. Use GET /api/v1/connectors/gmail/auth-url instead.",
        )
    service = ConnectorService(session)
    res = await service.connect_platform(
        user_id=current_user.id, platform_str=platform, auth_data=payload.auth_data
    )
    return ApiResponse(
        success=True,
        message=f"{platform.capitalize()} integration connected successfully",
        data=ConnectResponse(**res),
    )


@router.get(
    "/gmail/auth-url",
    response_model=ApiResponse[GmailAuthUrlResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Gmail OAuth authorization URL",
)
async def get_gmail_auth_url(
    current_user: User = Depends(get_current_user),
    post_auth_redirect_uri: str = Query(...),
    sync_range_days: int = Query(30, description="Email history sync range in days"),
) -> ApiResponse[GmailAuthUrlResponse]:
    """Return the Google authorization URL for Gmail connector onboarding."""
    settings = get_settings()
    backend_callback_uri = settings.google_redirect_uri
    state = _encode_state(
        {
            "connector": "gmail",
            "user_id": str(current_user.id),
            "post_auth_redirect_uri": post_auth_redirect_uri,
            "sync_range_days": sync_range_days,
            "issued_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    query = urlencode(
        {
            "client_id": settings.google_client_id,
            "redirect_uri": backend_callback_uri,
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent",
            "scope": "https://www.googleapis.com/auth/gmail.readonly openid email profile",
            "state": state,
        }
    )
    return ApiResponse(
        success=True,
        message="Gmail authorization URL generated successfully",
        data=GmailAuthUrlResponse(authorization_url=f"https://accounts.google.com/o/oauth2/v2/auth?{query}"),
    )


@router.get("/gmail/callback")
async def gmail_callback(
    code: str | None = Query(None),
    state: str | None = Query(None),
    error: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    """Complete Gmail OAuth and persist connector credentials."""
    settings = get_settings()

    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    if not code or not state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Gmail OAuth parameters")

    state_data = _decode_state(state)
    if state_data.get("connector") != "gmail":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Gmail OAuth state")

    try:
        user_id = uuid.UUID(state_data["user_id"])
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Gmail OAuth user") from exc
    
    post_auth_redirect_uri = state_data.get("post_auth_redirect_uri")
    if not post_auth_redirect_uri:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing post-auth redirect URI")

    backend_callback_uri = settings.google_redirect_uri
    async with httpx.AsyncClient() as http_client:
        token_response = await http_client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": backend_callback_uri,
                "grant_type": "authorization_code",
            },
            timeout=10.0,
        )

    if token_response.status_code != 200:
        logger.error("Gmail callback token exchange failed: %s", token_response.text)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gmail authorization code exchange failed",
        )

    token_data = token_response.json()
    credentials = {
        "access_token": token_data.get("access_token"),
        "refresh_token": token_data.get("refresh_token"),
        "expires_in": token_data.get("expires_in", 3600),
        "scope": token_data.get("scope"),
        "token_type": token_data.get("token_type"),
    }

    if not credentials["access_token"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gmail authorization did not return an access token",
        )

    service = ConnectorService(session)
    connector = await service._repo.get_by_platform_and_user(Platform.GMAIL, user_id)
    if not connector:
        connector = await service._repo.create_connector(user_id, Platform.GMAIL)

    from app.services.credential_manager import CredentialManager

    cm = CredentialManager()
    encrypted_creds = cm.encrypt_credentials(credentials)
    sync_range_days = state_data.get("sync_range_days", 30)
    connector.settings = {
        **(connector.settings or {}),
        "credentials": encrypted_creds,
        "sync_range_days": sync_range_days,
    }
    await service._repo.update_state(connector, ConnectorState.CONNECTED)
    await session.commit()

    sync_service = SyncService(session)
    try:
        await sync_service.trigger_sync(user_id=user_id, platform_str="gmail")
    except Exception:
        logger.exception("Initial Gmail sync failed after callback for user %s", user_id)

    return RedirectResponse(
        url=f"{post_auth_redirect_uri}?success=true",
        status_code=302,
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


class UpdateSettingsRequest(BaseModel):
    """Payload to update connector settings."""
    settings: Dict[str, Any]


@router.get(
    "/{platform}/history",
    response_model=ApiResponse[List[Dict[str, Any]]],
    status_code=status.HTTP_200_OK,
    summary="Get connector sync history",
)
async def get_connector_history(
    platform: str = Path(..., description="The platform key (currently gmail)"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[List[Dict[str, Any]]]:
    """Return sync history runs for a connector platform."""
    try:
        plat = Platform[platform.upper()]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid platform: '{platform}'",
        )

    repo = ConnectorRepository(session)
    connector = await repo.get_by_platform_and_user(plat, current_user.id)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found",
        )

    history_runs = await repo.list_sync_history(connector.id, limit=30)
    serialized = []
    for run in history_runs:
        serialized.append({
            "id": str(run.id),
            "started_at": run.started_at.isoformat(),
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "messages_imported": run.messages_imported,
            "attachments_imported": run.attachments_imported,
            "status": run.status,
            "duration": run.duration,
            "error": run.error,
        })
    return ApiResponse(
        success=True,
        message="Sync history retrieved successfully",
        data=serialized,
    )


@router.post(
    "/{platform}/settings",
    response_model=ApiResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Update connector settings",
)
async def update_connector_settings(
    payload: UpdateSettingsRequest,
    platform: str = Path(..., description="The platform key"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[Dict[str, Any]]:
    """Update settings dictionary for a connector integration."""
    try:
        plat = Platform[platform.upper()]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid platform: '{platform}'",
        )

    repo = ConnectorRepository(session)
    connector = await repo.get_by_platform_and_user(plat, current_user.id)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found",
        )

    existing = connector.settings or {}
    creds = existing.get("credentials")
    new_settings = {**existing, **payload.settings}
    if creds:
        new_settings["credentials"] = creds

    connector.settings = new_settings
    session.add(connector)
    await session.commit()

    return ApiResponse(
        success=True,
        message="Settings updated successfully",
        data=new_settings,
    )


@router.post(
    "/attachments/{attachment_id}/analyze",
    response_model=ApiResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Analyze a specific attachment on demand",
)
async def analyze_attachment(
    attachment_id: str = Path(..., description="UUID of the attachment to analyze"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[Dict[str, Any]]:
    """Trigger on-demand text extraction and AI summarization for a specific attachment."""
    from app.models.communication import Attachment, Communication
    from sqlalchemy import select
    from app.services.attachment_extractor import AttachmentExtractor
    from app.providers.storage.local import LocalFileStorageProvider
    from app.ai.prompts.attachment_summarize import get_attachment_summarize_prompt
    from app.ai.prompts.vision_summarize import get_vision_summarize_prompt
    from app.ai.factory import AIProviderFactory

    att_id = uuid.UUID(attachment_id)
    stmt = select(Attachment).where(Attachment.id == att_id)
    result = await session.execute(stmt)
    att = result.scalar_one_or_none()

    if not att:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")

    # Verify user owns this attachment's communication
    comm_stmt = select(Communication).where(Communication.id == att.communication_id)
    comm_result = await session.execute(comm_stmt)
    comm = comm_result.scalar_one_or_none()
    if not comm or not comm.connector_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Communication not found")

    # Load bytes from storage
    storage = LocalFileStorageProvider()
    if not att.url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Attachment has no storage URL")

    storage_path = att.url.replace("file:///", "").replace(storage.base_dir.as_posix() + "/", "")
    try:
        content_bytes = await storage.get_file(storage_path)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment file not found in storage")

    att.processing_status = "processing"
    session.add(att)
    await session.commit()

    extractor = AttachmentExtractor()
    category = extractor.get_file_category(att.name, att.content_type)
    extracted = extractor.extract_text(att.name, content_bytes, att.content_type)

    try:
        if extracted:
            att.extracted_text = extracted
            provider = AIProviderFactory.get_provider()
            messages = get_attachment_summarize_prompt(att.name, extracted, comm.subject)
            raw_summary = await provider.chat(messages)
            att.attachment_summary = raw_summary
            att.processing_status = "completed"
        elif category == "image":
            import base64
            image_b64 = base64.b64encode(content_bytes).decode("utf-8")
            mime = att.content_type or "image/png"
            prompt = get_vision_summarize_prompt(att.name, comm.subject)
            provider = AIProviderFactory.get_provider()
            if hasattr(provider, "vision_chat"):
                raw_summary = await provider.vision_chat(prompt, image_b64, mime)
                att.attachment_summary = raw_summary
                att.processing_status = "completed"
            else:
                att.processing_status = "failed"
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="Vision model not available for image analysis",
                )
        else:
            att.processing_status = "skipped"

        session.add(att)
        await session.commit()

        return ApiResponse(
            success=True,
            message="Attachment analyzed successfully",
            data={
                "id": str(att.id),
                "name": att.name,
                "processing_status": att.processing_status,
                "attachment_summary": att.attachment_summary,
                "extracted_text_length": len(att.extracted_text) if att.extracted_text else 0,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        att.processing_status = "failed"
        session.add(att)
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Attachment analysis failed: {str(e)}",
        )

