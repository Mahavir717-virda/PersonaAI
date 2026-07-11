"""Category classification helper for Communication Intelligence."""

from __future__ import annotations


class CategoryDetector:
    """Maps and standardizes message categories."""

    VALID_CATEGORIES = {"work", "personal", "finance", "social", "spam", "general"}

    @classmethod
    def clean_category(cls, category: str | None) -> str:
        """Standardizes raw category string."""
        if not category:
            return "general"
        val = category.strip().lower()
        return val if val in cls.VALID_CATEGORIES else "general"
