"""Resolves entity name variants to canonical identifiers."""

from __future__ import annotations

from typing import List, Optional


class EntityLinker:
    """Links entity variants (e.g., 'John Smith', 'John', 'Mr. Smith') to a canonical entity name."""

    @staticmethod
    def resolve_canonical_name(name: str, existing_names: List[str]) -> str:
        """Compares target name with existing canonical names, returning the resolved canonical name.

        If a strong match is identified (e.g., name is a token subset or substring),
        returns the existing canonical name. Otherwise, returns the original name.
        """
        cleaned_target = name.strip().lower()
        if not cleaned_target:
            return name

        # 1. Exact match ignore case
        for existing in existing_names:
            if existing.strip().lower() == cleaned_target:
                return existing

        # 2. Containment match (e.g. "John" matches "John Smith")
        # Ensure we match multi-word names appropriately to avoid linking dissimilar short words
        best_match: Optional[str] = None
        best_match_len = 0

        for existing in existing_names:
            cleaned_existing = existing.strip().lower()
            # If the target name is a sub-segment of an existing name (e.g. "John" -> "John Smith")
            if cleaned_target in cleaned_existing or cleaned_existing in cleaned_target:
                # Prefer the longer/more specific canonical name
                if len(existing) > best_match_len:
                    best_match = existing
                    best_match_len = len(existing)

        if best_match:
            # Let's ensure a sanity check: we don't merge short words like "is" or "in"
            if len(cleaned_target) > 2:
                return best_match

        return name
