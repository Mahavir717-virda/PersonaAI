"""Preprocesses email text context, cleaning signatures, HTML tags, and quote blocks."""

from __future__ import annotations

import re


class EmailPreprocessor:
    """Strips signature metadata, HTML markup, and quote replies to format clean prompts."""

    @staticmethod
    def clean_email_text(text: str) -> str:
        """Removes duplicate reply blocks, HTML elements, tracking links, and signature tags."""
        if not text:
            return ""

        # 1. Strip HTML tags
        cleaned = re.sub(r"<[^>]*>", " ", text)

        # 2. Strip tracking urls / links
        cleaned = re.sub(r"https?://\S+", "", cleaned)

        # 3. Strip quoted replies (lines starting with '>')
        lines = cleaned.split("\n")
        filtered_lines = []
        for line in lines:
            line_strip = line.strip()
            # Stop parsing if typical separator found
            if line_strip.startswith(">") or "--- Original Message ---" in line or "From:" in line:
                break
            
            # Skip signature blocks
            if line_strip == "--" or line_strip.lower() in {"thanks,", "regards,", "best regards,", "sincerely,"}:
                break
            
            filtered_lines.append(line)

        cleaned = "\n".join(filtered_lines)

        # 4. Collapse duplicate spaces / formatting
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        return cleaned
