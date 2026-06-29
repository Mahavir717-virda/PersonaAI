# PersonaAI Project

PersonaAI is a long-term production SaaS platform for AI-assisted personal productivity and automation. The current phase is backend bootstrapping only.

## Current Scope

- Establish a production-grade FastAPI backend foundation.
- Prepare async PostgreSQL connectivity through SQLAlchemy 2.0.
- Add typed environment configuration with Pydantic Settings.
- Add structured logging and HTTP middleware.
- Add Docker Compose services for local development.

## Explicitly Out of Scope

- Authentication and authorization.
- Gmail integration.
- AI orchestration.
- Embeddings, RAG, memory, and vector search behavior.
- Notifications, scheduler jobs, and workers.
- Business logic in routes or infrastructure packages.

Future feature work should preserve the architecture boundaries documented in `docs/ARCHITECTURE.md`.
