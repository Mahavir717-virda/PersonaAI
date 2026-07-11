"""Webhook API route handlers."""

import base64
import json
import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.repositories.user import UserRepository
from app.services.sync import SyncService
from app.schemas.response import ApiResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


class PubSubMessage(BaseModel):
    """Google Pub/Sub message wrapper."""

    data: str
    messageId: str


class PubSubPayload(BaseModel):
    """Google Pub/Sub push notification payload wrapper."""

    message: PubSubMessage
    subscription: str


@router.post(
    "/gmail",
    response_model=ApiResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Receive Google Gmail Pub/Sub push notifications",
)
async def gmail_push_webhook(
    payload: PubSubPayload,
    session: AsyncSession = Depends(get_session),
) -> ApiResponse[Dict[str, Any]]:
    """Receive live Gmail event notifications via Google Cloud Pub/Sub, scheduling an incremental sync."""
    try:
        # 1. Decode base64 Pub/Sub payload data
        decoded_bytes = base64.b64decode(payload.message.data)
        data_dict = json.loads(decoded_bytes.decode("utf-8"))
        email_address = data_dict.get("emailAddress")
        history_id = data_dict.get("historyId")

        logger.info(
            "[GmailWebhook] Received push event for email: %s, historyId: %s",
            email_address,
            history_id,
        )

        if not email_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="emailAddress missing in Pub/Sub data payload",
            )

        # 2. Look up user by email address
        user_repo = UserRepository(session)
        user = await user_repo.get_by_email(email_address)
        if not user:
            logger.warning("[GmailWebhook] No user found matching email address: %s", email_address)
            return ApiResponse(
                success=True,
                message="Event received, but no matching user found",
                data={"email": email_address, "history_id": history_id, "processed": False},
            )

        # 3. Trigger incremental synchronization cycle
        sync_service = SyncService(session)
        sync_result = await sync_service.trigger_sync(user_id=user.id, platform_str="gmail")

        return ApiResponse(
            success=True,
            message="Incremental sync triggered successfully",
            data={
                "email": email_address,
                "history_id": history_id,
                "sync_status": sync_result.get("status"),
                "messages_imported": sync_result.get("messages_imported", 0),
                "processed": True,
            },
        )
    except Exception as e:
        logger.exception("[GmailWebhook] Failed to process Google Pub/Sub event")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing error: {str(e)}",
        )
