# PersonaAI Architecture

PersonaAI uses a clean backend architecture designed for incremental SaaS growth. This bootstrap phase creates the structural contracts and operational foundation only; product features will be added in later phases.

## Backend Boundaries

- `api` contains FastAPI route registration and HTTP endpoints.
- `schemas` contains Pydantic request and response schemas.
- `services` will contain business workflows.
- `repositories` will contain database access logic.
- `models` will contain SQLAlchemy ORM tables.
- `database` contains SQLAlchemy engine, session, and declarative base setup.
- `config` contains typed environment-driven settings.
- `middleware` contains cross-cutting HTTP behavior.
- `startup` contains application lifecycle management.

Routes should remain thin. Business decisions belong in services, persistence details belong in repositories, and API validation belongs in schemas.

## Runtime Flow

1. `app.main:create_app` loads settings and configures logging.
2. Middleware is registered for CORS, request logging, timing, and unhandled exceptions.
3. Exception handlers provide consistent FastAPI error responses.
4. Request and correlation IDs are attached to every request.
5. Routers are registered for root and versioned endpoints.
6. Lifespan startup and shutdown manage application lifecycle resources.

## Communication Object

The central domain object is `Communication`. Connectors normalize raw platform data into this object before any future AI processing happens. This keeps Gmail, WhatsApp, Slack, Discord, documents, and future sources independent from the AI core.

## API Contracts

Public endpoints use explicit versioning through `/api/v1` and future `/api/v2` namespaces. Responses use shared envelopes so success and error payloads remain consistent across the platform.

## Authentication and OAuth

User authentication is handled via JWT (JSON Web Tokens). The backend provides endpoints for login, logout, and token refresh.

For connecting to third-party services, PersonaAI uses a client-aware OAuth 2.0 flow that supports multiple clients (Web, Chrome Extension, etc.) from a single set of backend endpoints. For a detailed explanation of this flow, see [OAuth 2.0 Architecture](./OAUTH_FLOW.md).

## Database

The database layer is prepared for PostgreSQL through SQLAlchemy 2.0 async primitives:

- Async engine
- Async session factory
- Declarative base
- Request-scoped session dependency

No models or migrations are created in this phase.

## Future Feature Areas

The packages for authentication, AI, connectors, embeddings, RAG, memory, notifications, scheduling, workers, search, and vector storage are intentionally present but contain no business logic yet. They provide stable ownership boundaries for future implementation phases.
