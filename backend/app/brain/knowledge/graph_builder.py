"""Compiles entities and relationships into clean nodes and edges."""

from __future__ import annotations

from typing import Any, Dict, List
from uuid import uuid4


class GraphBuilder:
    """Compiles extracted facts into graph representation nodes and edges."""

    @staticmethod
    def build_graph_elements(
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Converts normalized entities and relationships into a node/edge graph dictionary."""
        nodes = []
        node_map = {}

        # 1. Compile Nodes
        for ent in entities:
            name = ent.get("name")
            if not name:
                continue
            
            node_id = str(uuid4())
            node_element = {
                "id": node_id,
                "label": name,
                "type": ent.get("type", "Concept"),
                "properties": ent.get("properties") or {}
            }
            nodes.append(node_element)
            node_map[name.lower()] = node_id

        # 2. Compile Edges
        edges = []
        for rel in relationships:
            sub_name = rel.get("subject", "").lower()
            obj_name = rel.get("object", "").lower()

            sub_id = node_map.get(sub_name)
            obj_id = node_map.get(obj_name)

            if sub_id and obj_id:
                edges.append({
                    "id": str(uuid4()),
                    "source_id": sub_id,
                    "target_id": obj_id,
                    "relation_type": rel.get("predicate", "related_to"),
                    "properties": rel.get("properties") or {}
                })

        return {"nodes": nodes, "edges": edges}
