"""General chat prompts."""

def get_general_chat_prompt(user_query: str, history: list[dict[str, str]] | None = None) -> list[dict[str, str]]:
    """Formulates the prompt chain for a general chat interaction, incorporating session history."""
    system_instruction = (
        "You are PersonaAI, an advanced agentic assistant. Help the user with their requests. "
        "Be concise, clear, and professional."
    )
    messages = [{"role": "system", "content": system_instruction}]
    if history:
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_query})
    return messages
