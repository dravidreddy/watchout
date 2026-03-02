"""
Smart Preference Conflict Resolution
Detects user corrections and replaces instead of appends
Prevents circular clarification loops and bloated itineraries
"""
from typing import Dict, Any, Optional, Tuple
import re


class PreferenceReducer:
    """
    Handles preference updates with intelligent conflict resolution.

    Detects user intent:
    - 'replace': User is correcting/changing previous preference
    - 'add': User is adding to existing preferences
    """

    # Keywords that indicate user is correcting/replacing previous input
    REPLACEMENT_KEYWORDS = [
        # English
        "instead", "actually", "change", "no wait", "i mean",
        "correction", "rather", "switch to", "replace", "not",
        "different", "other", "another", "nevermind", "wrong",
        "meant to say", "scratch that", "forget", "cancel",

        # Hindi (romanized)
        "nahi", "nahin", "balki", "waise",

        # Hindi (Devanagari)
        "नहीं", "बल्कि", "वैसे",
    ]

    # Keywords that indicate addition/expansion
    ADDITION_KEYWORDS = [
        "also", "and", "plus", "additionally", "too",
        "as well", "along with", "moreover", "furthermore",
        "include", "add",

        # Hindi
        "aur", "और", "bhi", "भी", "saath", "साथ",
    ]

    def __init__(self):
        # Create regex patterns for fast matching
        self.replacement_pattern = re.compile(
            r'\b(' + '|'.join(re.escape(kw) for kw in self.REPLACEMENT_KEYWORDS) + r')\b',
            re.IGNORECASE,
        )
        self.addition_pattern = re.compile(
            r'\b(' + '|'.join(re.escape(kw) for kw in self.ADDITION_KEYWORDS) + r')\b',
            re.IGNORECASE,
        )

    def detect_intent(self, user_message: str) -> str:
        """
        Detect if user is:
        - 'replace': Correcting previous preference
        - 'add': Adding to existing preferences

        Returns:
            'replace' | 'add'
        """
        msg_lower = user_message.lower()
        msg_casefold = user_message.casefold()

        has_replacement = bool(self.replacement_pattern.search(user_message))
        has_addition = bool(self.addition_pattern.search(user_message))

        # Python's \b semantics can miss some non-ASCII scripts; include a
        # conservative fallback for non-ASCII keywords.
        if not has_replacement:
            has_replacement = any(
                (not kw.isascii()) and (kw.casefold() in msg_casefold)
                for kw in self.REPLACEMENT_KEYWORDS
            )
        if not has_addition:
            has_addition = any(
                (not kw.isascii()) and (kw.casefold() in msg_casefold)
                for kw in self.ADDITION_KEYWORDS
            )

        if has_replacement and not has_addition:
            return "replace"
        if has_addition and not has_replacement:
            return "add"
        if has_replacement and has_addition:
            # Both signals present - prioritize replacement (safer default)
            return "replace"

        # No explicit signal - use heuristics
        if (" and " in msg_lower or "," in user_message) and " or " not in msg_lower:
            return "add"
        return "replace"

    def update_preferences(
        self,
        current: Dict[str, Any],
        new: Dict[str, Any],
        user_message: str,
    ) -> Tuple[Dict[str, Any], str]:
        """
        Smart merge preferences based on user intent.

        Returns:
            (updated_preferences, change_summary)
        """
        intent = self.detect_intent(user_message)
        changes = []
        updated = current.copy()

        for key, new_value in new.items():
            old_value = current.get(key)

            # Handle list-type preferences (destinations, activities, cuisines)
            if isinstance(new_value, list):
                if intent == "replace":
                    updated[key] = new_value
                    if old_value:
                        changes.append(f"Changed {key} from {old_value} to {new_value}")
                    else:
                        changes.append(f"Set {key} to {new_value}")
                else:  # add
                    existing = set(current.get(key, []))
                    merged = current.get(key, []) + [v for v in new_value if v not in existing]
                    updated[key] = merged
                    new_items = [v for v in new_value if v not in existing]
                    if new_items:
                        changes.append(f"Added {new_items} to {key}")
                    else:
                        changes.append(f"{key} already includes {new_value}")

            # Handle scalar preferences (duration, budget, start_date)
            else:
                updated[key] = new_value
                if old_value and old_value != new_value:
                    changes.append(f"Updated {key} from '{old_value}' to '{new_value}'")
                else:
                    changes.append(f"Set {key} to '{new_value}'")

        summary = "; ".join(changes) if changes else "No changes"
        return updated, summary

    def generate_confirmation(self, changes_summary: str, intent: str) -> str:
        """Generate user-friendly confirmation message."""
        if intent == "replace":
            return f"✅ Got it! {changes_summary}"
        return f"✅ Added! {changes_summary}"

    def should_clarify(
        self,
        current: Dict[str, Any],
        new: Dict[str, Any],
        user_message: str,
    ) -> Optional[str]:
        """
        Determine if we should ask for clarification.

        Returns:
            Clarification question or None
        """
        intent = self.detect_intent(user_message)

        # Only clarify if truly ambiguous (has both signals and conflicting data)
        if intent == "unknown":
            for key in new.keys():
                if key in current and current[key] != new[key]:
                    old_val = current[key]
                    new_val = new[key]
                    if isinstance(new_val, list) and isinstance(old_val, list):
                        return (
                            f"I noticed you mentioned {new_val}. "
                            f"Should I replace {old_val} or add {new_val} to your preferences?"
                        )

        return None


# Singleton instance
preference_reducer = PreferenceReducer()
