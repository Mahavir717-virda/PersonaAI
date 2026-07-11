"""Prompt templates for Task Extraction and dependency analysis."""

TASK_EXTRACTION_PROMPT = """Analyze the text and extract all tasks, deadlines, and dependencies.
Response MUST be a JSON array of objects with keys:
- title: string (the action, e.g. "Prepare Q3 budget presentation")
- owner: string (who is responsible, e.g. "John")
- priority: string ("low", "medium", "high")
- deadline: string (relative or absolute target date, e.g. "Friday" or "2026-07-03")
- status: string ("pending", "completed")
- depends_on: array of strings (titles of tasks that this task depends on)

Text: {text}
JSON Output:"""
