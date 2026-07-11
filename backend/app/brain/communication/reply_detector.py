"""Detects reply necessity, decisions, tasks, meetings, and deadlines."""

from __future__ import annotations


class ReplyDetector:
    """Evaluates text patterns to predict downstream processing requirements."""

    @classmethod
    def evaluate_triggers(cls, text: str) -> dict[str, bool]:
        """Runs heuristic checks on input string to detect structural components."""
        cleaned = text.strip().lower()

        # Direct triggers
        has_question = "?" in cleaned or any(w in cleaned for w in ["who", "what", "when", "where", "why", "how", "can you"])
        has_task_words = any(w in cleaned for w in ["please", "need to", "task", "todo", "action", "do this", "send", "submit"])
        has_deadline_words = any(w in cleaned for w in ["before", "by friday", "deadline", "due", "by next", "until"])
        has_meeting_words = any(w in cleaned for w in ["meet", "meeting", "call", "zoom", "schedule", "calendar", "invite"])
        has_decision_words = any(w in cleaned for w in ["approved", "decided", "reject", "confirmed", "agreed"])

        return {
            "requires_reply": bool(has_question or has_task_words or has_meeting_words),
            "contains_task": bool(has_task_words),
            "contains_deadline": bool(has_deadline_words),
            "contains_decision": bool(has_decision_words),
            "contains_meeting": bool(has_meeting_words),
        }
