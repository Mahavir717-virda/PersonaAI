# Connector Architecture

PersonaAI connectors convert platform-specific records into a single normalized communication object.

## Core Principle

The AI engine should process `Communication`, not Gmail messages, Slack events, WhatsApp chats, or Discord messages directly.

```text
Platform Record -> Connector -> Communication -> PersonaAI Engine
```

## Base Connector

Future connectors inherit from `BaseConnector` and implement:

- `connect`
- `disconnect`
- `fetch`
- `normalize`

The `normalize` method returns the canonical `Communication` model from `backend/app/core/communication.py`.

## Current Scope

No Gmail, WhatsApp, Slack, Discord, OAuth, or synchronization logic exists yet. This phase only defines the connector contract.
