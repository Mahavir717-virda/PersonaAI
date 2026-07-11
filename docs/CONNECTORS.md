# Connector Architecture

PersonaAI connectors convert platform-specific records into a single normalized `Communication` object. This ensures the core AI engine operates on a consistent data model, regardless of the data source.

## Core Principle

The AI engine should process a `Communication` object, not Gmail messages, Slack events, or WhatsApp chats directly.

```text
Platform Record -> Connector -> Communication -> PersonaAI Engine
```

## Connector Lifecycle and State

Each connector instance has a lifecycle managed by the backend. The state of a connector is always visible to the user in the UI. For a detailed breakdown of the states, see the [Connector Lifecycle section in the OAuth Flow documentation](./OAUTH_FLOW.md#5-connector-lifecycle).

## OAuth 2.0 for Connectors

For platforms that use OAuth 2.0 (like Gmail), PersonaAI employs a centralized, client-aware authentication flow. This allows different clients (the Web Dashboard, Chrome Extension, etc.) to use the same backend endpoints for connecting their accounts.

For a detailed explanation of the multi-client OAuth flow, including sequence diagrams and security considerations, see the **[PersonaAI OAuth 2.0 Architecture](./OAUTH_FLOW.md)** document.

## Base Connector

All connectors inherit from a `BaseConnector` class and implement a standard interface. This ensures that the `ConnectorService` can manage all connectors in a consistent way.

The conceptual `BaseConnector` interface includes methods for:

- `authorize`: Handling authentication, either via OAuth or other methods (e.g., API keys).
- `disconnect`: Revoking credentials and cleaning up resources.
- `sync`: Fetching data from the platform and normalizing it into `Communication` objects.
- `health`: Checking the validity of the stored credentials.

The `sync` method is responsible for fetching the data and passing it to a `CommunicationPipeline` for processing and storage.
