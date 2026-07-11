"""Prompt templates for Entity Extraction and normalization."""

ENTITY_EXTRACTION_PROMPT = """Analyze the text and extract all entities.
For each entity, output:
- value: string (exact matched text, e.g. "John", "Atlas")
- type: string ("Person", "Project", "Organization", "Location", "Date", "Event", "Concept")
- start_char: number (character offset starting from 0)
- end_char: number (character offset ending character)
- canonical_name: string (predicted full canonical representation, e.g. "John Smith")
- confidence: number (0.0 to 1.0)

Response MUST be a JSON array of objects with keys:
[
  {{
    "value": "...",
    "type": "...",
    "start_char": ...,
    "end_char": ...,
    "canonical_name": "...",
    "confidence": ...
  }}
]

Text: {text}
JSON Output:"""
