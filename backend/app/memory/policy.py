"""Privacy and security policy configurations for memory ingestion."""

from __future__ import annotations

import re


class MemoryPolicy:
    """Enforces privacy rules to block passwords, credit cards, or OTPs from being remembered."""

    # Simple regex patterns matching sensitive credentials
    PASSWORD_PATTERN = re.compile(
        r"\b(password|pass|passwd|secret|token|api[-_]?key|auth[-_]?key|credentials|private[-_]?key)\b\s*[:=]\s*\S+",
        re.IGNORECASE
    )
    CREDIT_CARD_PATTERN = re.compile(
        r"\b(?:\d[ -]*?){13,16}\b"
    )
    OTP_PATTERN = re.compile(
        r"\b(otp|one[-_]?time[-_]?password|verification[-_]?code|2fa|mfa)\b.*?\b\d{4,8}\b",
        re.IGNORECASE
    )

    @classmethod
    def should_store(cls, content: str) -> bool:
        """Evaluates whether content complies with privacy policies."""
        cleaned = content.strip()
        
        # 1. Block passwords
        if cls.PASSWORD_PATTERN.search(cleaned):
            return False
            
        # 2. Block credit card numbers
        if cls.CREDIT_CARD_PATTERN.search(cleaned):
            return False
            
        # 3. Block OTP codes
        if cls.OTP_PATTERN.search(cleaned):
            return False
            
        # Standard filter checks: prevent saving generic short nonsense
        if len(cleaned) < 3:
            return False
            
        return True
