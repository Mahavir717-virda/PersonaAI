"""Gmail Provider SDK wrapper implementation."""

import asyncio
import base64
import logging
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List

import httpx

from app.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class GmailProvider(BaseProvider):
    """Integrates with Google Gmail REST API using raw OAuth Access Tokens."""

    def __init__(self) -> None:
        self.last_sync_cursor: str | None = None

    @staticmethod
    def _decode_base64_urlsafe(data: str) -> bytes:
        """Decode Gmail base64url payloads with relaxed padding handling."""
        padding = "=" * (-len(data) % 4)
        return base64.urlsafe_b64decode(data + padding)

    async def _fetch_attachment_content(
        self,
        client: httpx.AsyncClient,
        headers: dict[str, str],
        message_id: str,
        attachment_id: str,
    ) -> str:
        """Fetch a Gmail attachment body and return its base64url data."""
        attachment_resp = await client.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/"
            f"{message_id}/attachments/{attachment_id}",
            headers=headers,
            timeout=10.0,
        )
        attachment_resp.raise_for_status()
        attachment_data = attachment_resp.json().get("data", "")
        return attachment_data

    async def _fetch_message_detail(
        self,
        client: httpx.AsyncClient,
        headers: dict[str, str],
        message_id: str,
    ) -> dict[str, Any]:
        """Fetch a Gmail message detail payload and normalize it for PersonaAI."""
        detail_resp = await client.get(
            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}",
            headers=headers,
            params={"format": "full"},
            timeout=10.0,
        )
        detail_resp.raise_for_status()

        msg_data = detail_resp.json()
        payload = msg_data.get("payload", {})
        headers_list = payload.get("headers", [])
        header_map = {h["name"].lower(): h["value"] for h in headers_list}
        labels = msg_data.get("labelIds", [])

        body_parts: list[str] = []
        attachments: list[dict[str, Any]] = []

        async def extract_parts(part: dict[str, Any]) -> None:
            body = part.get("body", {})
            if body.get("data"):
                body_parts.append(body["data"])
            attachment_id = body.get("attachmentId")
            if part.get("filename") and attachment_id:
                attachment_data = await self._fetch_attachment_content(
                    client=client,
                    headers=headers,
                    message_id=message_id,
                    attachment_id=attachment_id,
                )
                attachments.append(
                    {
                        "name": part["filename"],
                        "content_type": part.get("mimeType"),
                        "size_bytes": body.get("size", 0),
                        "attachment_id": attachment_id,
                        "content_base64": attachment_data,
                    }
                )
            for child in part.get("parts", []):
                await extract_parts(child)

        await extract_parts(payload)

        body_text = ""
        if body_parts:
            try:
                raw_bytes = self._decode_base64_urlsafe(body_parts[0])
                body_text = raw_bytes.decode("utf-8", errors="ignore")
            except Exception:
                body_text = ""
        else:
            body_data = payload.get("body", {}).get("data", "")
            if body_data:
                try:
                    raw_bytes = self._decode_base64_urlsafe(body_data)
                    body_text = raw_bytes.decode("utf-8", errors="ignore")
                except Exception:
                    body_text = ""

        return {
            "id": msg_data["id"],
            "thread_id": msg_data["threadId"],
            "history_id": msg_data.get("historyId"),
            "subject": header_map.get("subject", "(No Subject)"),
            "body": body_text or "No body content",
            "sender_name": header_map.get("from", "Unknown"),
            "sender_address": header_map.get("from", ""),
            "recipient_address": header_map.get("to", ""),
            "attachments": attachments,
            "date": header_map.get("date", datetime.now().isoformat()),
            "labels": labels,
            "snippet": msg_data.get("snippet"),
            "unread": "UNREAD" in labels,
        }

    async def fetch_messages_page(
        self, credentials: dict[str, Any], cursor: str | None = None
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Fetch one page of Gmail messages and return the provider cursor."""
        token = credentials.get("token")
        if not token:
            logger.warning("[GmailProvider] Missing access token for message page fetch")
            return [], None

        headers = {"Authorization": f"Bearer {token}"}
        params: dict[str, Any] = {"maxResults": 50}
        if cursor:
            params["pageToken"] = cursor

        async with httpx.AsyncClient() as client:
            list_resp = await client.get(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                headers=headers,
                params=params,
                timeout=10.0,
            )
            list_resp.raise_for_status()

            list_data = list_resp.json()
            message_list = list_data.get("messages", [])
            next_page_token = list_data.get("nextPageToken")
            logger.info("[GmailProvider] Calling Gmail API for message page; fetched %s message stubs", len(message_list))
            records = await asyncio.gather(
                *(self._fetch_message_detail(client, headers, item["id"]) for item in message_list)
            )

            logger.info("[GmailProvider] Messages fetched: %s", len(records))
            history_ids = [record.get("history_id") for record in records if record.get("history_id")]
            self.last_sync_cursor = max(history_ids, key=lambda value: int(value)) if history_ids else cursor
            return records, next_page_token

    async def fetch_messages_since_history(
        self, credentials: dict[str, Any], history_id: str
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Fetch Gmail changes since the last stored history checkpoint."""
        token = credentials.get("token")
        if not token:
            logger.warning("[GmailProvider] Missing access token for history sync")
            self.last_sync_cursor = history_id
            return

        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient() as client:
            seen_ids: set[str] = set()
            message_ids: list[str] = []

            page_token: str | None = None
            latest_history_id: str | None = None
            while True:
                params: dict[str, Any] = {
                    "startHistoryId": history_id,
                    "maxResults": 100,
                }
                if page_token:
                    params["pageToken"] = page_token

                resp = await client.get(
                    "https://gmail.googleapis.com/gmail/v1/users/me/history",
                    headers=headers,
                    params=params,
                    timeout=10.0,
                )
                resp.raise_for_status()

                data = resp.json()
                history_records = data.get("history", [])
                latest_history_id = data.get("historyId") or latest_history_id or history_id

                for history_entry in history_records:
                    for key in ("messagesAdded", "labelsAdded", "labelsRemoved", "messagesDeleted"):
                        for item in history_entry.get(key, []):
                            message = item.get("message") or {}
                            message_id = message.get("id")
                            if message_id and message_id not in seen_ids and key != "messagesDeleted":
                                seen_ids.add(message_id)
                                message_ids.append(message_id)

                page_token = data.get("nextPageToken")
                if not page_token:
                    break

            self.last_sync_cursor = latest_history_id or history_id

            records = await asyncio.gather(
                *(self._fetch_message_detail(client, headers, message_id) for message_id in message_ids)
            )

            logger.info(
                "[GmailProvider] History sync fetched %s changed messages since %s",
                len(records),
                history_id,
            )
            for record in records:
                yield record

    async def fetch_messages(
        self, credentials: dict[str, Any], cursor: str | None = None
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Fetch real emails from the user's Gmail inbox with pagination support."""
        current_cursor = cursor
        latest_history_id: str | None = None
        while True:
            records, next_cursor = await self.fetch_messages_page(credentials, current_cursor)
            for record in records:
                history_id = record.get("history_id")
                if history_id:
                    if latest_history_id is None or int(history_id) > int(latest_history_id):
                        latest_history_id = history_id
                yield record
            if not next_cursor or next_cursor == current_cursor:
                break
            current_cursor = next_cursor
        self.last_sync_cursor = latest_history_id or current_cursor

    async def verify_credentials(self, credentials: dict[str, Any]) -> bool:
        """Call Google UserInfo API endpoint to verify token validity."""
        token = credentials.get("token")
        if not token:
            return False
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v3/userinfo",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5.0,
                )
                return response.status_code == 200
            except Exception as e:
                logger.error(f"[GmailProvider] Credential validation failed: {str(e)}")
                return False

    async def fetch_labels(self, credentials: dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch labels configured in Gmail account."""
        token = credentials.get("token")
        if not token:
            return []
        
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://gmail.googleapis.com/gmail/v1/users/me/labels",
                headers=headers,
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json().get("labels", [])

    async def fetch_threads(self, credentials: dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch thread listings in user Gmail inbox."""
        token = credentials.get("token")
        if not token:
            return []
        
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://gmail.googleapis.com/gmail/v1/users/me/threads",
                headers=headers,
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json().get("threads", [])

    async def fetch_attachments(
        self, credentials: dict[str, Any], message_id: str
    ) -> List[Dict[str, Any]]:
        """Fetch attachment metadata and contents for a Gmail message."""
        token = credentials.get("token")
        if not token:
            return []

        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}",
                headers=headers,
                params={"format": "full"},
                timeout=10.0,
            )
            resp.raise_for_status()

            message = resp.json()
            payload = message.get("payload", {})
            attachments: list[Dict[str, Any]] = []

            async def collect_parts(part: dict[str, Any]) -> None:
                body = part.get("body", {})
                attachment_id = body.get("attachmentId")
                if part.get("filename") and attachment_id:
                    attachment_resp = await client.get(
                        "https://gmail.googleapis.com/gmail/v1/users/me/messages/"
                        f"{message_id}/attachments/{attachment_id}",
                        headers=headers,
                        timeout=10.0,
                    )
                    attachment_resp.raise_for_status()
                    attachments.append(
                        {
                            "name": part["filename"],
                            "content_type": part.get("mimeType"),
                            "size_bytes": body.get("size", 0),
                            "attachment_id": attachment_id,
                            "content_base64": attachment_resp.json().get("data", ""),
                        }
                    )
                for child in part.get("parts", []):
                    await collect_parts(child)

            await collect_parts(payload)
            return attachments
