from app.brain.models import (
    AIAction,
    AIThought,
    BrainRun,
    BrainSession,
    BrainState,
    ConversationSummary,
    EmbeddingChunk,
    Fact,
    Insight,
    Knowledge,
    KnowledgeRelation,
    Memory,
    Reminder,
    RetrievalLog,
    Task,
    UserPreference,
)


def test_brain_models_are_registered_on_metadata() -> None:
    expected_tables = {
        "brain_sessions",
        "brain_runs",
        "brain_states",
        "tasks",
        "reminders",
        "insights",
        "facts",
        "user_preferences",
        "conversation_summaries",
        "ai_actions",
        "ai_thoughts",
        "retrieval_logs",
        "embedding_chunks",
        "memories",
        "knowledge",
        "knowledge_relations",
    }

    assert expected_tables.issubset(set(BrainSession.__table__.metadata.tables.keys()))
    assert BrainSession.__tablename__ == "brain_sessions"
    assert BrainRun.__tablename__ == "brain_runs"
    assert Memory.__tablename__ == "memories"
    assert Knowledge.__tablename__ == "knowledge"
    assert KnowledgeRelation.__tablename__ == "knowledge_relations"
    assert EmbeddingChunk.__tablename__ == "embedding_chunks"
    assert AIAction.__tablename__ == "ai_actions"
    assert AIThought.__tablename__ == "ai_thoughts"
    assert RetrievalLog.__tablename__ == "retrieval_logs"
    assert UserPreference.__tablename__ == "user_preferences"
