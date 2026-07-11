"""Task extraction prompts."""

def get_task_extraction_prompt(text: str) -> list[dict[str, str]]:
    """Returns prompt messages for extracting actionable tasks and deadlines."""
    system_instruction = (
        "You are PersonaAI, an intelligent email assistant. "
        "Extract all actionable tasks, action items, and associated deadlines from the provided text. "
        "Return the result ONLY as a JSON object with a single key 'tasks' which contains a list of strings. "
        "Example output:\n"
        "{\n"
        "  \"tasks\": [\n"
        "    \"Submit budget proposal by Friday\",\n"
        "    \"Schedule follow-up meeting with Sarah\"\n"
        "  ]\n"
        "}\n"
        "Do not include any conversational filler, markdown formatting, or wrappers."
    )
    return [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": f"Extract tasks from this text:\n\n{text}"}
    ]
