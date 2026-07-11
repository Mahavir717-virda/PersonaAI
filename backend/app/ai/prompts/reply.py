"""Smart reply generation prompts."""

def get_reply_prompt(original_text: str, tone: str = "professional") -> list[dict[str, str]]:
    """Returns prompt messages for generating context-aware smart replies."""
    system_instruction = (
        f"You are PersonaAI, an intelligent email assistant. "
        f"Draft a concise, helpful, and natural reply to the provided email/message. "
        f"The tone of the response must be: {tone}. "
        "Provide only the draft message body without subject lines, salutations, or sign-offs unless requested."
    )
    return [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": f"Message to reply to:\n\n{original_text}"}
    ]
