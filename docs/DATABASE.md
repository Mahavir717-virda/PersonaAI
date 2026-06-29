# Database Design

PersonaAI is prepared for PostgreSQL through SQLAlchemy 2.0 async primitives.

## Current Foundation

- Async SQLAlchemy engine.
- Async session factory.
- Declarative base class.
- Request-scoped database session dependency.
- Database health check using `SELECT 1`.

## Boundaries

- ORM table classes belong in `backend/app/models/`.
- Database access belongs in `backend/app/repositories/`.
- Business workflows belong in `backend/app/services/`.
- Routes should not directly perform database queries.

## Future Work

Alembic is declared as part of the stack but migrations have not been initialized yet. pgvector support is part of the product roadmap and should be added when embeddings and semantic search are implemented.
