"""Normalizes variant entity names and maps aliases."""

from __future__ import annotations

from typing import Any, Dict, List


class EntityNormalizer:
    """Normalizes variant references to a single canonical entity name and records aliases."""

    @staticmethod
    def normalize_variants(
        extracted_entities: List[Dict[str, Any]],
        existing_entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Compares incoming entity values against existing entity logs to consolidate aliases."""
        normalized = list(existing_entities)

        for incoming in extracted_entities:
            val = incoming.get("value", "")
            ent_type = incoming.get("type", "Concept")
            canonical = incoming.get("canonical_name", val)

            # Check if canonical name or value already matches an existing entry
            matched_entry = None
            for entry in normalized:
                # Direct match on canonical name or values / aliases
                existing_canonical = entry.get("canonical_name", "").lower()
                existing_aliases = [a.lower() for a in entry.get("aliases", [])]
                
                if (canonical.lower() == existing_canonical or 
                    val.lower() == existing_canonical or 
                    val.lower() in existing_aliases or
                    # Substring check for persons or projects (e.g., "John" matches "John Smith")
                    (len(val) > 2 and val.lower() in existing_canonical) or
                    (len(existing_canonical) > 2 and existing_canonical in val.lower())):
                    matched_entry = entry
                    break

            if matched_entry:
                # Merge logic
                aliases = set(matched_entry.get("aliases", []))
                aliases.add(val)
                aliases.add(canonical)
                if val in aliases and val == matched_entry["canonical_name"]:
                    pass  # keep existing longer canonical
                elif len(canonical) > len(matched_entry["canonical_name"]):
                    matched_entry["canonical_name"] = canonical

                matched_entry["aliases"] = list(aliases)
                matched_entry["occurrences"] = matched_entry.get("occurrences", 1) + 1
                matched_entry["confidence"] = min(1.0, (matched_entry.get("confidence", 1.0) + incoming.get("confidence", 1.0)) / 2.0)
            else:
                # Create a new canonical entry
                normalized.append({
                    "canonical_name": canonical,
                    "type": ent_type,
                    "aliases": [val, canonical] if val != canonical else [val],
                    "occurrences": 1,
                    "confidence": incoming.get("confidence", 1.0),
                    "metadata": incoming.get("properties", {})
                })

        return normalized
