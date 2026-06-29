# AI Engine

The AI engine is intentionally not implemented in this phase.

## Future Responsibility

The future AI engine will process normalized `Communication` objects and produce:

- Summaries.
- Extracted tasks.
- Detected deadlines.
- Meeting insights.
- Decisions.
- Semantic search results.
- Conversational memory.

## Boundary Rule

AI code should not depend on platform-specific connector payloads. Connectors must normalize raw platform data first, then pass `Communication` objects into the AI layer.

## Current Scope

The packages for `ai`, `embeddings`, `rag`, `memory`, `search`, and `vector` exist as ownership boundaries only. They contain no AI business logic yet.
