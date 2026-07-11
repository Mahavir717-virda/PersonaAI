"""Resolves relative date references (e.g. 'tomorrow', 'Friday') into datetime objects."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


class DeadlineResolver:
    """Parses relative time references into absolute timezone-aware datetime objects."""

    @staticmethod
    def resolve_relative_deadline(reference: str, current_time: datetime | None = None) -> datetime | None:
        """Parses words like 'tomorrow', 'Friday', 'next Monday' to datetime."""
        now = current_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        cleaned = reference.strip().lower()
        if not cleaned:
            return None

        # 1. tomorrow
        if cleaned == "tomorrow":
            return now + timedelta(days=1)

        # 2. today
        if cleaned == "today":
            return now

        # Weekdays lookup
        weekdays = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }

        # 3. next weekday / next Monday
        for day_name, day_idx in weekdays.items():
            if day_name in cleaned:
                days_ahead = day_idx - now.weekday()
                if days_ahead <= 0:  # Target day already passed this week
                    days_ahead += 7
                if "next" in cleaned:
                    days_ahead += 7
                return now + timedelta(days=days_ahead)

        # 4. Standard ISO string fallback
        try:
            val = datetime.fromisoformat(cleaned)
            if val.tzinfo is None:
                val = val.replace(tzinfo=timezone.utc)
            return val
        except ValueError:
            return None
