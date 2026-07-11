"""Calendar event detection prompts."""

def get_calendar_detection_prompt(text: str) -> list[dict[str, str]]:
    """Returns prompt messages for detecting calendar events from text."""
    system_instruction = (
        "You are PersonaAI. Parse the text and identify any scheduled events, meetings, or appointments. "
        "Return the result ONLY as a JSON object of this structure:\n"
        "{\n"
        "  \"events\": [\n"
        "    {\n"
        "      \"title\": \"Event Title\",\n"
        "      \"start_time\": \"Mentioned start time or ISO representation if clear\",\n"
        "      \"end_time\": \"Mentioned end time or null\",\n"
        "      \"attendees\": [\"people mentioned as attendees\"],\n"
        "      \"location\": \"location or null\"\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "Do not include other content or markdown wrappers."
    )
    return [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": f"Parse calendar events from:\n\n{text}"}
    ]
