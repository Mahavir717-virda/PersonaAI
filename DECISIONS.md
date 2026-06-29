# Decisions

## Backend Framework

FastAPI is the backend framework for this phase because it provides first-class async support, OpenAPI documentation, dependency injection, and strong typing ergonomics.

## Configuration

Pydantic Settings is used for environment-driven configuration across development, testing, and production.

## Database

PostgreSQL is the primary relational database. SQLAlchemy 2.0 async primitives provide the engine, session factory, and declarative base.

## Containers

Docker Compose is the local orchestration target. It includes the API, PostgreSQL, pgAdmin, and Ollama with named volumes and health checks.

## Central Communication Model

All connectors will normalize source-specific data into a single `Communication` domain object before AI processing. This prevents the AI core from depending on Gmail, WhatsApp, Slack, Discord, or future platform-specific payloads.

## API Versioning

Public routes are organized under explicit version namespaces. Version 1 lives under `/api/v1`; version 2 is reserved for future breaking changes.
