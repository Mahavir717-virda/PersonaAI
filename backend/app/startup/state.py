"""Application runtime state management."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI


@dataclass(slots=True)
class RuntimeState:
    """Runtime resources attached to the FastAPI app."""

    started_at: datetime
    database: Any | None = None
    ollama_client: Any | None = None
    embedding_model: Any | None = None
    scheduler: Any | None = None


def initialize_runtime_state(app: FastAPI) -> RuntimeState:
    """Create and attach application runtime state."""
    runtime_state = getattr(app.state, "runtime", None)
    if runtime_state is None:
        runtime_state = RuntimeState(started_at=datetime.now(tz=UTC))
        app.state.runtime = runtime_state
    return runtime_state


def get_runtime_state(app: FastAPI) -> RuntimeState:
    """Return the application runtime state, creating it if missing."""
    runtime_state = getattr(app.state, "runtime", None)
    if runtime_state is None:
        runtime_state = initialize_runtime_state(app)
    return runtime_state
