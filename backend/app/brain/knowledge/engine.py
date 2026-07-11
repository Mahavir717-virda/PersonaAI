"""Implementation of the KnowledgeEngine."""

from __future__ import annotations

from app.brain.engines.base import BrainEngine
from app.brain.schemas.state import BrainState
from app.database.session import async_session_factory
from app.brain.knowledge.repository import KnowledgeRepository
from app.brain.knowledge.retriever import KnowledgeRetriever
from app.brain.knowledge.extractor import KnowledgeExtractor
from app.brain.knowledge.entity_linker import EntityLinker
from app.brain.knowledge.relationship_builder import RelationshipBuilder
from app.brain.knowledge.graph_builder import GraphBuilder
from app.brain.knowledge.validator import FactValidator
from app.brain.knowledge.confidence import KnowledgeConfidence


class KnowledgeEngine(BrainEngine):
    """Knowledge Engine implementing extraction, conflict checking, linking, and subgraph retrieves."""

    def __init__(
        self,
        extractor: KnowledgeExtractor | None = None,
        validator: FactValidator | None = None,
    ) -> None:
        self.extractor = extractor or KnowledgeExtractor()
        self.validator = validator or FactValidator()

    @property
    def name(self) -> str:
        return "knowledge"

    async def execute(self, state: BrainState) -> BrainState:
        incoming = state.conversation.incoming_message
        if not incoming or not incoming.content:
            return state

        query_text = incoming.content
        user_id = state.context.user_profile.user_id

        async with async_session_factory() as session:
            repository = KnowledgeRepository(session)
            retriever = KnowledgeRetriever(repository)

            # 1. Retrieve relevant active subgraph context
            factual_context = await retriever.retrieve_factual_context(user_id, query_text)

            # 2. Extract new entities and relationships from incoming text
            extracted_entities = await self.extractor.extract_entities(
                text=query_text,
                model=state.model_routing.selected_model,
            )

            if extracted_entities:
                # Load all existing active nodes to support entity linking
                active_nodes = await repository.get_active_nodes(user_id)
                existing_titles = [n.title for n in active_nodes]

                # Link entity variants
                for ent in extracted_entities:
                    canonical_name = EntityLinker.resolve_canonical_name(
                        ent["name"], existing_titles
                    )
                    ent["name"] = canonical_name

                    # 3. Check for existing node conflicts
                    existing_node = await repository.get_node_by_title(user_id, canonical_name)
                    if existing_node:
                        # Validate conflict or update
                        new_content = ent.get("properties", {}).get("description", query_text)
                        resolution = await self.validator.resolve_conflict(
                            existing_fact=existing_node.content,
                            incoming_fact=new_content,
                        )

                        if resolution.get("resolution") == "supersede_a_with_b":
                            # Supersede old node and create a new node
                            new_node = await repository.create_node(
                                user_id=user_id,
                                title=canonical_name,
                                content=new_content,
                                knowledge_type=ent.get("type", "Concept"),
                                source="conversation",
                                metadata={"lifecycle_stage": "validated"},
                            )
                            await repository.resolve_supersedence(
                                old_node=existing_node,
                                new_node_id=new_node.id,
                                reason=resolution.get("explanation"),
                            )
                    else:
                        # Create new canonical node
                        await repository.create_node(
                            user_id=user_id,
                            title=canonical_name,
                            content=ent.get("properties", {}).get("description", query_text),
                            knowledge_type=ent.get("type", "Concept"),
                            source="conversation",
                            metadata={"lifecycle_stage": "created"},
                        )

            # Ingest relational triples if any extracted
            extracted_relations = await self.extractor.extract_relationships(
                text=query_text,
                model=state.model_routing.selected_model,
            )
            if extracted_relations:
                active_nodes = await repository.get_active_nodes(user_id)
                existing_titles = [n.title for n in active_nodes]

                builder = RelationshipBuilder()
                triples = builder.build_triples(extracted_relations, existing_titles)

                for triple in triples:
                    sub_node = await repository.get_node_by_title(user_id, triple["subject"])
                    obj_node = await repository.get_node_by_title(user_id, triple["object"])

                    if sub_node and obj_node:
                        await repository.create_relation(
                            source_id=sub_node.id,
                            target_id=obj_node.id,
                            relation_type=triple["predicate"],
                            metadata=triple["properties"],
                        )

            # Append retrieved graph facts to prompt response context
            if factual_context:
                existing_context = state.response.context or ""
                separator = "\n\n" if existing_context else ""
                new_context = (
                    f"{existing_context}{separator}"
                    f"### Retrieved Graph Facts:\n{factual_context}"
                )
                updated_response = state.response.model_copy(update={
                    "context": new_context
                })
                return state.update(response=updated_response)

            return state

    async def validate(self, state: BrainState) -> bool:
        return state.context.user_profile.user_id is not None

    async def rollback(self, state: BrainState) -> BrainState:
        return state
