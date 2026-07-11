"""Prompt templates for Communication Intelligence analysis."""

COMMUNICATION_CLASSIFICATION_PROMPT = """Analyze the incoming communication text.
Determine classification values across intent, emotion, urgency, priority, tone, category, and downstream triggers.

Response MUST be JSON format with keys:
- intent: string (e.g. "request", "inform", "greeting", "question", "apology", "complaint")
- emotion: string (e.g. "neutral", "happy", "frustrated", "anxious", "grateful")
- urgency: string ("low", "medium", "high")
- priority: string ("low", "medium", "high")
- tone: string (e.g. "professional", "casual", "urgent", "polite")
- category: string (e.g. "work", "personal", "finance", "social", "spam")
- requires_reply: boolean (does this message need an AI reply?)
- contains_task: boolean (does this message contain commitments/actions?)
- contains_deadline: boolean (does this message specify a target date/time limit?)
- contains_decision: boolean (does this message record an approval or decision?)
- contains_meeting: boolean (does this message propose or talk about meetings?)
- confidence: number (0.0 to 1.0 classification confidence)

Text: {text}
JSON Output:"""
