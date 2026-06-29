# Architecture

See `docs/ARCHITECTURE.md` for the detailed backend architecture overview.

The short version: PersonaAI follows a clean backend architecture where routes handle HTTP, schemas validate API payloads, services own business workflows, repositories own persistence, models represent database tables, and utilities remain stateless.
