"""Prompt templates for Knowledge Graph extraction and conflict resolution."""

ENTITY_EXTRACTION_PROMPT = """Analyze the text and extract all significant entities.
Return a JSON array of objects with keys:
- name: string (canonical entity name, e.g., "John Smith")
- type: string (e.g., "Person", "Project", "Organization", "Location", "Date", "Event", "Concept")
- properties: object (key-value attributes)

Text: {text}
JSON Output:"""

RELATIONSHIP_EXTRACTION_PROMPT = """Analyze the text and extract all factual subject-predicate-object relationships.
Return a JSON array of objects with keys:
- subject: string (name of source entity)
- predicate: string (relationship type, e.g., "approved", "works_on", "belongs_to", "deadline_at")
- object: string (name of target entity)
- properties: object (key-value attributes)

Text: {text}
JSON Output:"""

CONFLICT_RESOLUTION_PROMPT = """You are analyzing two conflicting facts in a Knowledge Graph.
Fact A: {fact_a}
Fact B: {fact_b}

Determine which fact is more recent, accurate, or if one supersedes the other.
Return JSON format with keys:
- has_conflict: boolean
- resolution: string ("supersede_a_with_b", "supersede_b_with_a", "merge", "no_action")
- merged_content: string (if merged, write the consolidated fact; otherwise empty)
- explanation: string (why this resolution was selected)
JSON Output:"""
