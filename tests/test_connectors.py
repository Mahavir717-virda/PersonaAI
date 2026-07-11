"""Unit and integration tests for the Universal Connector Framework."""

import asyncio
import base64
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
import uuid

from app.connectors.registry import ConnectorRegistry
from app.connectors.factory import ConnectorFactory
from app.connectors.gmail import GmailConnector
from app.connectors.whatsapp import WhatsAppConnector
from app.models.communication import Communication, Participant, Attachment
from app.enums.platform import Platform
from app.services.credential_manager import CredentialManager
from app.events.bus import EventBus
from app.communication.gmail.infrastructure.provider.gmail_provider import GmailProvider


def test_connector_registration():
    """Verify connectors are registered automatically under their platform keys."""
    gmail_cls = ConnectorRegistry.get("GMAIL")
    whatsapp_cls = ConnectorRegistry.get("WHATSAPP")
    
    assert gmail_cls is GmailConnector
    assert whatsapp_cls is WhatsAppConnector


def test_connector_factory_creation():
    """Verify the ConnectorFactory instantiates the correct connector classes."""
    gmail_client = ConnectorFactory.create("GMAIL")
    whatsapp_client = ConnectorFactory.create("WHATSAPP")

    assert isinstance(gmail_client, GmailConnector)
    assert isinstance(whatsapp_client, WhatsAppConnector)

    with pytest.raises(ValueError):
        ConnectorFactory.create("NON_EXISTENT_PLATFORM")


def test_gmail_manifest_contents():
    """Verify Gmail connector manifest fields and capability flags."""
    manifest = GmailConnector.get_manifest()

    assert manifest.id == "gmail"
    assert manifest.name == "Google Gmail"
    assert manifest.supports_oauth is True
    assert manifest.capabilities.supports_drafts is True
    assert manifest.capabilities.supports_streaming is False


def test_gmail_payload_normalization():
    """Verify raw Gmail JSON payloads normalize to nested Communication models."""
    async def run_test():
        raw_payload = {
            "id": "gmail_test_100",
            "thread_id": "thread_test_100",
            "subject": "Hello World",
            "body": "This is a body text.",
            "sender_name": "Alice Bob",
            "sender_address": "alice@example.com",
            "recipient_address": "bob@example.com",
            "attachments": [
                {
                    "name": "document.pdf",
                    "content_type": "application/pdf",
                    "size_bytes": 1024,
                }
            ],
            "date": datetime.now(timezone.utc).isoformat(),
        }

        connector = GmailConnector()
        comm = await connector.normalize(raw_payload)

        assert isinstance(comm, Communication)
        assert comm.platform == Platform.GMAIL
        assert comm.platform_message_id == "gmail_test_100"
        assert comm.subject == "Hello World"
        assert comm.body == "This is a body text."

        # Validate nested participants
        assert len(comm.participants) == 2
        sender = next(p for p in comm.participants if p.type == "sender")
        assert sender.name == "Alice Bob"
        assert sender.address == "alice@example.com"

        # Validate nested attachments
        assert len(comm.attachments) == 1
        att = comm.attachments[0]
        assert att.name == "document.pdf"
        assert att.content_type == "application/pdf"
        assert att.size_bytes == 1024

    asyncio.run(run_test())


def test_credential_manager_symmetric_encryption():
    """Verify CredentialManager encrypts and decrypts dictionaries successfully."""
    cm = CredentialManager()
    data = {"access_token": "secret123", "refresh_token": "refresh456"}
    
    encrypted = cm.encrypt_credentials(data)
    assert encrypted.startswith("fernet:")
    
    decrypted = cm.decrypt_credentials(encrypted)
    assert decrypted["access_token"] == "secret123"
    assert decrypted["refresh_token"] == "refresh456"


def test_credential_manager_legacy_encryption_compatibility():
    """Verify legacy base64 credential payloads still decrypt correctly."""
    cm = CredentialManager()
    legacy_payload = base64.b64encode(
        b'{"access_token":"legacy-token","refresh_token":"legacy-refresh"}'
    ).decode("utf-8")

    decrypted = cm.decrypt_credentials(f"enc_{legacy_payload}")

    assert decrypted["access_token"] == "legacy-token"
    assert decrypted["refresh_token"] == "legacy-refresh"


@patch("app.communication.gmail.infrastructure.provider.gmail_provider.httpx.AsyncClient")
def test_gmail_provider_fetches_attachment_bytes(mock_client_class):
    """Verify Gmail provider downloads attachment content from the Gmail API."""

    async def run_test():
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        def make_response(payload):
            return SimpleNamespace(
                status_code=200,
                json=lambda: payload,
                raise_for_status=lambda: None,
            )

        async def get_side_effect(url, **kwargs):
            if url.endswith("/messages"):
                return make_response(
                    {
                        "messages": [{"id": "msg-1"}],
                        "nextPageToken": None,
                    }
                )
            if url.endswith("/messages/msg-1"):
                return make_response(
                    {
                        "id": "msg-1",
                        "threadId": "thread-1",
                        "payload": {
                            "headers": [
                                {"name": "Subject", "value": "Hello"},
                                {"name": "From", "value": "Alice <alice@example.com>"},
                                {"name": "To", "value": "Bob <bob@example.com>"},
                                {"name": "Date", "value": "Mon, 01 Jan 2024 00:00:00 +0000"},
                            ],
                            "parts": [
                                {
                                    "filename": "report.pdf",
                                    "mimeType": "application/pdf",
                                    "body": {"attachmentId": "att-1", "size": 4},
                                }
                            ],
                        },
                        "labelIds": ["INBOX"],
                        "snippet": "snippet",
                    }
                )
            if url.endswith("/attachments/att-1"):
                return make_response({"data": "cmVhbC1ieXRlcw"})
            raise AssertionError(f"Unexpected Gmail API URL: {url}")

        mock_client.get.side_effect = get_side_effect

        provider = GmailProvider()
        records, next_cursor, failed = await provider.fetch_messages_page(
            {"token": "access-token"}
        )

        assert next_cursor is None
        assert records[0]["attachments"][0]["attachment_id"] == "att-1"
        assert records[0]["attachments"][0]["content_base64"] == "cmVhbC1ieXRlcw"
        assert records[0]["body"] == "No body content"

    asyncio.run(run_test())



def test_event_bus_publishing():
    """Verify EventBus triggers correct callbacks on matching event types."""
    bus = EventBus()
    received_events = []

    class DummyEvent:
        pass

    def on_dummy_event(event):
        received_events.append(event)

    bus.subscribe(DummyEvent, on_dummy_event)
    
    async def run_publish():
        event = DummyEvent()
        await bus.publish(event)

    asyncio.run(run_publish())
    assert len(received_events) == 1
