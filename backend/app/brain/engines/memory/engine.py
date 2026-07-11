"""Advanced implementation of the MemoryEngine with policy filtering, lifecycle, decay, and dynamic justifications."""

from __future__ import annotations

from typing import List, Dict

from app.brain.engines.base import BrainEngine
from app.brain.schemas.state import BrainState, MemoryState, MemoryLifecycleStage
from app.database.session import async_session_factory
from app.repositories.memory import MemoryRepository
from app.embeddings.provider import OllamaEmbeddingProvider
from app.memory.scorer import MemoryScorer
from app.memory.policy import MemoryPolicy
from app.memory.context_builder import MemoryContextBuilder


class MemoryEngine(BrainEngine):
    """Advanced Memory Engine executing retrieval pipelines, custom decay curves, and telemetry logging."""

    def __init__(
        self,
        embedding_provider: OllamaEmbeddingProvider | None = None,
        scorer: MemoryScorer | None = None,
    ) -> None:
        self.embedding_provider = embedding_provider or OllamaEmbeddingProvider()
        self.scorer = scorer or MemoryScorer()

    @property
    def name(self) -> str:
        return "memory"

    async def execute(self, state: BrainState) -> BrainState:
        incoming = state.conversation.incoming_message
        if not incoming or not incoming.content:
            return state

        query_text = incoming.content
        user_id = state.context.user_profile.user_id

        # 1. Enforce privacy policy rules on incoming query to prevent leaking sensitive items
        if not MemoryPolicy.should_store(query_text):
            return state

        async with async_session_factory() as session:
            repository = MemoryRepository(session)
            
            # 2. Generate vector query
            query_vector = await self.embedding_provider.get_embedding(
                text=query_text,
                model=state.model_routing.selected_embedding,
            )

            # 3. Vector search
            raw_results = await repository.vector_search_memories(
                user_id=user_id,
                query_vector=query_vector,
                limit=15,
            )

            # 4. Multi-dimensional scoring & custom decay curves
            working: List[str] = []
            episodic: List[str] = []
            semantic: List[str] = []
            procedural: List[str] = []
            flat_memories: List[str] = []
            scores: Dict[str, float] = {}
            reasons: Dict[str, str] = {}
            lifecycle_stages: Dict[str, MemoryLifecycleStage] = {}
            links: Dict[str, List[str]] = {}

            for memory, similarity in raw_results:
                final_score = self.scorer.score_memory(memory, similarity)
                
                # Filter out irrelevant candidates
                if final_score < 0.35:
                    continue

                content = memory.content
                flat_memories.append(content)
                scores[content] = final_score

                # Determine retrieval reason justifications
                meta = memory.metadata_ or {}
                reasons[content] = (
                    f"similarity={similarity:.2f}; "
                    f"recency_boost={meta.get('importance', 0.5):.2f}; "
                    f"access_frequency={meta.get('access_count', 0)}; "
                    f"pinned={meta.get('pinned', False)}"
                )
                
                # Read lifecycle stage and links
                stage_val = meta.get("lifecycle_stage", MemoryLifecycleStage.CREATED.value)
                try:
                    lifecycle_stages[content] = MemoryLifecycleStage(stage_val)
                except ValueError:
                    lifecycle_stages[content] = MemoryLifecycleStage.CREATED
                    
                links[content] = [str(uid) for uid in meta.get("links", [])]

                # Categorize based on Memory Lifecycle
                if memory.memory_type == "working":
                    working.append(content)
                elif memory.memory_type == "episodic":
                    episodic.append(content)
                elif memory.memory_type == "procedural":
                    procedural.append(content)
                else:
                    semantic.append(content)

            # 5. Format compact prompt context via ContextBuilder
            compiled_context = MemoryContextBuilder.build_context(
                working=working,
                episodic=episodic,
                semantic=semantic,
                procedural=procedural,
                top_k=5,
            )

            new_memory_state = MemoryState(
                working_memory=working,
                episodic_memory=episodic,
                semantic_memory=semantic,
                procedural_memory=procedural,
                retrieved_memories=flat_memories,
                memory_score=scores,
                short_term=working,
                long_term=episodic + semantic + procedural,
                retrieval_reasons=reasons,
                lifecycle_stages=lifecycle_stages,
                links=links,
                compiled_context=compiled_context,
                confidence=float(sum(scores.values()) / len(scores)) if scores else 1.0,
            )

            # Injected into the response context as well to make it accessible to Response node
            new_response_state = state.response.model_copy(update={
                "context": compiled_context
            })

            return state.update(memory=new_memory_state, response=new_response_state)

    async def validate(self, state: BrainState) -> bool:
        return state.context.user_profile.user_id is not None

    async def rollback(self, state: BrainState) -> BrainState:
        return state
