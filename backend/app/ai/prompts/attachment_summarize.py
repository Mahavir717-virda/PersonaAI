"""Attachment summarization prompts for text-based documents."""


def get_attachment_summarize_prompt(
    filename: str,
    extracted_text: str,
    email_subject: str | None = None,
) -> list[dict[str, str]]:
    """Returns structured prompt messages to summarize an extracted attachment."""
    context_line = ""
    if email_subject:
        context_line = f"\nThis attachment was sent as part of an email with subject: \"{email_subject}\"\n"

    system_instruction = (
        "You are PersonaAI, an intelligent email assistant. "
        "You are given the extracted text content of a file attachment from an email. "
        "Analyze the document and respond ONLY with a valid JSON object matching this schema:\n"
        "{\n"
        '  "summary": "Brief 2-3 sentence description of the document\'s content and purpose.",\n'
        '  "key_points": ["important point 1", "important point 2"],\n'
        '  "document_type": "assignment | invoice | report | spreadsheet | letter | form | contract | receipt | other",\n'
        '  "deadlines": ["any deadline dates or due dates found"],\n'
        '  "action_items": ["tasks or actions derived from the document"],\n'
        '  "people": ["names of people mentioned"],\n'
        '  "amounts": ["any monetary amounts, totals, or figures mentioned"],\n'
        '  "metadata": {\n'
        '    "estimated_pages": null,\n'
        '    "language": "en",\n'
        '    "confidence": "high | medium | low"\n'
        "  }\n"
        "}\n"
        "Do NOT include any markdown code blocks, backticks, or prefix explanation. "
        "Respond with raw JSON only."
    )

    user_message = (
        f"Filename: {filename}"
        f"{context_line}\n"
        f"--- Extracted Document Content ---\n{extracted_text}"
    )

    return [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_message},
    ]
