"""Summarization prompts."""

def get_summarize_prompt(conversation_text: str) -> list[dict[str, str]]:
    """Returns the structured prompt messages to generate an email summary."""
    system_instruction = (
        "You are PersonaAI, an intelligent email assistant. Summarize the provided email or conversation thread. "
        "You must respond ONLY with a valid JSON object matching this schema:\n"
        "{\n"
        "  \"tldr\": \"Very short summary sentence under 15 words.\",\n"
        "  \"summary\": \"A short paragraph summarizing the primary context and events.\",\n"
        "  \"key_points\": [\"list\", \"of\", \"key\", \"takeaways\"],\n"
        "  \"decisions\": [\"decisions made or agreed upon\"],\n"
        "  \"action_items\": [\"action items / tasks assigned to individuals\"],\n"
        "  \"deadlines\": [\"any mentioned dates/times representing deadlines\"],\n"
        "  \"people\": [\"names of people involved\"],\n"
        "  \"organizations\": [\"organizations/companies mentioned\"],\n"
        "  \"projects\": [\"specific projects or topics discussed\"],\n"
        "  \"meetings\": [\"meetings scheduled or planned\"],\n"
        "  \"risks\": [\"potential issues or risks highlighted\"],\n"
        "  \"follow_ups\": [\"follow-up actions required\"],\n"
        "  \"questions\": [\"questions left open or asked\"],\n"
        "  \"topics\": [\"general tags/topics of the thread\"]\n"
        "}\n"
        "Ensure all JSON strings are properly escaped. Do not wrap the JSON in markdown code blocks like ```json."
    )
    return [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": f"Please summarize this conversation thread:\n\n{conversation_text}"}
    ]
