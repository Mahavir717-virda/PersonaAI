"""StateGraph Orchestrator builder using LangGraph for the PersonaAI Brain."""

from __future__ import annotations

import time
from typing import Any, Dict

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from app.brain.orchestrator.dependencies import BrainContainer
from app.brain.orchestrator.router import BrainRouter
from app.brain.orchestrator.executor import GraphExecutor
from app.brain.schemas.state import BrainState
from app.brain.events.brain_events import NodeStarted, NodeCompleted, NodeFailed


def create_engine_node(engine_name: str, container: BrainContainer) -> Any:
    """Wraps a registered engine execute method with observability logging."""
    async def node_fn(state: BrainState) -> BrainState:
        start_time = time.time()
        engine = container.get(engine_name)
        
        # Increment execution depth & track active node
        visited = list(state.execution.visited_nodes) + [engine_name]
        updated_execution = state.execution.model_copy(update={
            "current_node": engine_name,
            "previous_node": state.execution.current_node,
            "visited_nodes": visited,
            "execution_depth": state.execution.execution_depth + 1,
        })
        state = state.update(execution=updated_execution)
        
        try:
            # Execute the engine
            result_state = await engine.execute(state)
            
            # Log success metrics
            final_state = GraphExecutor.log_node_execution(
                state=result_state,
                node_name=engine_name,
                start_time=start_time,
                success=True,
            )
            return final_state
            
        except Exception as e:
            # Log failure metrics
            final_state = GraphExecutor.log_node_execution(
                state=state,
                node_name=engine_name,
                start_time=start_time,
                success=False,
                error_message=str(e),
            )
            return final_state

    return node_fn


def build_brain_graph(container: BrainContainer, checkpointer: Any = None) -> Any:
    """Builds and compiles the LangGraph StateGraph with all engines and routing rules."""
    # 1. Initialize StateGraph with BrainState schema
    builder = StateGraph(BrainState)

    # 2. Add engine nodes
    engines = ["memory", "knowledge", "reasoning", "communication", "entity", "task", "planning", "rag", "response", "learning"]
    for engine in engines:
        builder.add_node(engine, create_engine_node(engine, container))

    # 3. Wire execution flows and conditional routing
    builder.add_edge(START, "memory")

    # Conditional routing after Memory
    builder.add_conditional_edges(
        "memory",
        BrainRouter.route_after_memory,
        {
            "knowledge": "knowledge",
            "response": "response",
        }
    )

    # Sequential steps
    builder.add_edge("knowledge", "reasoning")
    builder.add_edge("reasoning", "communication")
    builder.add_edge("communication", "entity")
    builder.add_edge("entity", "task")
    builder.add_edge("task", "planning")

    # Conditional routing after Planning
    builder.add_conditional_edges(
        "planning",
        BrainRouter.route_after_planning,
        {
            "rag": "rag",
            "response": "response",
        }
    )

    builder.add_edge("rag", "response")

    # Conditional routing after Response (checks reflection for loops or learning updates)
    builder.add_conditional_edges(
        "response",
        BrainRouter.route_after_response,
        {
            "learning": "learning",
            "START": "memory",  # Loop back for search retry
        }
    )

    builder.add_edge("learning", END)

    # 4. Compile with checkpointer
    if checkpointer is None:
        checkpointer = MemorySaver()
        
    return builder.compile(checkpointer=checkpointer)
