"""Gmail platform connector implementation."""

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import uuid
from collections.abc import AsyncIterator
from typing import Any, cast
import httpx

from app.connectors.base import BaseConnector
from app.connectors.manifest import ConnectorManifest, ConnectorCapabilities
from app.connectors.registry import ConnectorRegistry
from app.models.communication import Communication, Participant, Attachment
from app.enums.platform import Platform
from app.enums.communication_status import CommunicationStatus
from app.communication.gmail.infrastructure.provider.gmail_provider import GmailProvider
from app.config.config import get_settings


class GmailConnector(BaseConnector):
    """Google Gmail connector client wrapper."""

    _manifest = ConnectorManifest(
        id="gmail",
        name="Google Gmail",
        version="1.0.0",
        supports_oauth=True,
        supports_webhooks=True,
        supports_sync=True,
        required_scopes=["https://www.googleapis.com/auth/gmail.readonly"],
        icon="Mail",
        capabilities=ConnectorCapabilities(
            supports_search=True,
            supports_labels=True,
            supports_attachments=True,
            supports_threads=True,
            supports_push=True,
            supports_streaming=False,
            supports_drafts=True,
        ),
    )

    def __init__(self) -> None:
        self.credentials: dict[str, Any] = {}
        self.connected = False
        self.provider = GmailProvider()
        self.last_sync_cursor: str | None = None
        self.failed_sync_ids: list[str] = []

    @classmethod
    def get_manifest(cls) -> ConnectorManifest:
        return cls._manifest

    async def connect(self, credentials: dict[str, Any]) -> None:
        self.credentials = credentials
        self.connected = True

    async def disconnect(self) -> None:
        self.credentials = {}
        self.connected = False

    async def authorize(self, auth_data: dict[str, Any]) -> dict[str, Any]:
        """Exchange Google authorization code or register OAuth credentials dynamically."""
        code = auth_data.get("code")
        if code:
            settings = get_settings()
            redirect_uri = settings.google_redirect_uri.replace(
                "/auth/google/callback", "/connectors/gmail/callback"
            )
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "code": code,
                        "client_id": settings.google_client_id,
                        "client_secret": settings.google_client_secret,
                        "redirect_uri": redirect_uri,
                        "grant_type": "authorization_code",
                    },
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "access_token": data.get("access_token"),
                        "refresh_token": data.get("refresh_token"),
                        "expires_in": data.get("expires_in", 3600),
                    }
                else:
                    raise RuntimeError(
                        f"Google Token endpoint returned HTTP {resp.status_code}: {resp.text}"
                    )

        if "access_token" in auth_data:
            return {
                "access_token": auth_data["access_token"],
                "refresh_token": auth_data.get("refresh_token"),
                "expires_in": auth_data.get("expires_in", 3600),
            }

        raise ValueError(
            "Missing Google authorization code or access token credentials"
        )

    async def refresh_credentials(self, credentials: dict[str, Any]) -> dict[str, Any]:
        """Rotate expired access token using the refresh token."""
        refresh_token = credentials.get("refresh_token")
        if not refresh_token:
            raise ValueError("No refresh token present for credential rotation")

        settings = get_settings()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "refresh_token": refresh_token,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "grant_type": "refresh_token",
                },
                timeout=10.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    **credentials,
                    "access_token": data.get("access_token"),
                    "expires_in": data.get("expires_in", 3600),
                }
            else:
                raise RuntimeError(f"Google refresh token request failed: {resp.text}")

    async def health(self) -> bool:
        if not self.credentials.get("access_token"):
            return False
        return await self.provider.verify_credentials(
            {"token": self.credentials.get("access_token")}
        )

    async def fetch_messages(
        self, cursor: str | None = None
    ) -> tuple[list[dict[str, Any]], str | None]:
        return await self.provider.fetch_messages_page(
            {"token": self.credentials.get("access_token")},
            cursor=cursor,
        )

    async def fetch_threads(
        self, cursor: str | None = None
    ) -> tuple[list[dict[str, Any]], str | None]:
        return [], None

    async def fetch_attachments(self, message_id: str) -> list[dict[str, Any]]:
        return await self.provider.fetch_attachments(
            {"token": self.credentials.get("access_token")},
            message_id,
        )

    def sync(self, cursor: str | None = None) -> AsyncIterator[dict[str, Any]]:
        async def iterator() -> AsyncIterator[dict[str, Any]]:
            credentials = {"token": self.credentials.get("access_token")}
            self.failed_sync_ids.clear()

            if cursor:
                try:
                    async for record in self.provider.fetch_messages_since_history(
                        credentials, cursor
                    ):
                        yield record
                    self.last_sync_cursor = self.provider.last_sync_cursor
                    self.failed_sync_ids.extend(self.provider.get_failed_ids())
                    return
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code not in {400, 404, 410}:
                        raise

            async for record in self.provider.fetch_messages(credentials, cursor=None):
                yield record
            self.last_sync_cursor = self.provider.last_sync_cursor
            self.failed_sync_ids.extend(self.provider.get_failed_ids())

        return iterator()

    def get_failed_ids(self) -> list[str]:
        """Return the list of message IDs that failed to fetch during the last sync."""
        return self.failed_sync_ids

    async def normalize(self, raw_data: dict[str, Any]) -> Communication:
        attachments_data = cast(list[dict[str, Any]], raw_data.get("attachments", []))
        label_ids = cast(list[str], raw_data.get("labels", []))
        raw_date = raw_data.get("date")
        parsed_date = datetime.now().astimezone()
        if isinstance(raw_date, str) and raw_date:
            try:
                parsed_date = parsedate_to_datetime(raw_date)
                if parsed_date.tzinfo is None:
                    parsed_date = parsed_date.replace(tzinfo=timezone.utc)
            except Exception:
                parsed_date = datetime.now().astimezone()
        communication = Communication(
            id=uuid.uuid4(),
            platform=Platform.GMAIL,
            platform_message_id=raw_data["id"],
            subject=raw_data["subject"],
            body=raw_data["body"],
            status=CommunicationStatus.NEW,
            importance="medium",
            created_at=parsed_date,
            metadata_fields={
                "thread_id": raw_data["thread_id"],
                "labels": label_ids,
                "snippet": raw_data.get("snippet"),
                "unread": raw_data.get("unread", False),
            },
        )

        sender = Participant(
            id=uuid.uuid4(),
            name=raw_data["sender_name"],
            address=raw_data["sender_address"],
            type="sender",
        )
        communication.participants.append(sender)

        receiver = Participant(
            id=uuid.uuid4(),
            address=raw_data["recipient_address"],
            type="recipient",
        )
        communication.participants.append(receiver)

        for att in attachments_data:
            attachment = Attachment(
                id=uuid.uuid4(),
                name=att["name"],
                content_type=att["content_type"],
                size_bytes=att["size_bytes"],
            )
            communication.attachments.append(attachment)

        return communication


ConnectorRegistry.register("GMAIL", GmailConnector)
