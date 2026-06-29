# Coding Standards

## Python

- Use Python 3.12 or newer.
- Use type hints for function signatures and public module variables.
- Add docstrings to modules, public classes, and public functions.
- Keep routes thin; move business workflows to services.
- Keep database access in repositories.
- Keep utility functions stateless.
- Prefer async APIs for I/O-bound work.

## Architecture

- Do not implement business logic in routes, models, schemas, middleware, or configuration modules.
- Do not introduce authentication, AI, connector, worker, scheduler, or notification behavior during bootstrap.
- Avoid duplicated logic and premature abstractions.
- Keep configuration environment-driven and never hardcode secrets.
