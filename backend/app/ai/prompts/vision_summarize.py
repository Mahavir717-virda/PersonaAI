"""Vision model prompts for image-based attachment analysis."""


def get_vision_summarize_prompt(filename: str, email_subject: str | None = None) -> str:
    """Returns the text prompt sent alongside the image to the vision model."""
    context_line = ""
    if email_subject:
        context_line = f'\nThis image was attached to an email with subject: "{email_subject}".\n'

    return (
        "You are PersonaAI, an intelligent email assistant. "
        "Analyze this image attachment and respond ONLY with a valid JSON object matching this schema:\n"
        "{\n"
        '  "summary": "Brief 2-3 sentence description of what the image shows.",\n'
        '  "key_points": ["important visual element 1", "important visual element 2"],\n'
        '  "document_type": "diagram | chart | screenshot | photo | invoice | receipt | form | handwritten | other",\n'
        '  "text_found": ["any text or labels visible in the image"],\n'
        '  "people": ["names visible in the image, if any"],\n'
        '  "amounts": ["any monetary amounts visible"],\n'
        '  "metadata": {\n'
        '    "has_text": true,\n'
        '    "confidence": "high | medium | low"\n'
        "  }\n"
        "}\n"
        "Do NOT include any markdown code blocks, backticks, or prefix explanation. "
        "Respond with raw JSON only.\n"
        f"\nFilename: {filename}"
        f"{context_line}"
    )
