"""
Watchout Backend - Clarification Agent (5-Step Funnel)

New onboarding flow:
  Phase 1 → Ask 3 bundled questions (destination + duration + group) in ONE message
  Phase 2 → If destination unknown: show 3 curated destination suggestions as cards
  Phase 3 → Destination picked: ask vibe + budget in ONE message
  Phase 4 → All 5 fields known → is_complete = True → generate itinerary

Principles:
  - Never ask more than one topic per turn (but bundle related sub-questions)
  - Never repeat a question the user has already answered
  - Never end every message with the same canned closing line
  - Feel like a conversation, not a form
"""
from typing import Dict, Any, Optional, List

from app.agents.base import BaseAgent
from app.prompts import build_clarification_extraction_prompt


# Core fields — must be collected before generation (reduced from 11 → 5)
REQUIRED_FIELDS = [
    "destinations",
    "duration_days",
    "num_travelers",
    "budget_range",
    "travel_vibe",
]


def _compute_onboarding_phase(prefs: Dict[str, Any]) -> str:
    """
    Deterministically compute which funnel phase we're in based on what
    we already know. This drives the LLM prompt, not the LLM itself.
    """
    has_destination = bool(prefs.get("destinations")) and not (
        isinstance(prefs.get("destinations"), list)
        and prefs["destinations"] == ["agent_surprise"]
    )
    has_duration = prefs.get("duration_days") is not None
    has_travelers = prefs.get("num_travelers") is not None
    has_vibe = bool(prefs.get("travel_vibe"))
    has_budget = bool(prefs.get("budget_range"))

    # Phase 4: everything known → ready
    if has_destination and has_duration and has_travelers and has_vibe and has_budget:
        return "phase_4_ready"

    # Phase 3: destination known, collecting vibe/budget
    if has_destination and (has_duration or has_travelers):
        return "phase_3_personalization"

    # Phase 2: user asked for suggestions (destination == agent_surprise) or
    #          explicitly said they don't know
    if prefs.get("destination_open") or (
        isinstance(prefs.get("destinations"), list)
        and "agent_surprise" in prefs["destinations"]
    ):
        return "phase_2_suggestions"

    # Phase 1: first contact, know little or nothing
    return "phase_1_intake"


class ClarificationAgent(BaseAgent):
    """
    5-step funnel clarification agent.
    Gathers only 5 core fields using at most 3 conversational turns.
    """

    def __init__(self):
        super().__init__(
            name="Travel Buddy",
            description=(
                "You are Watchout, a warm and enthusiastic Indian travel companion. "
                "Your job is to learn what kind of trip the user wants in the fewest, "
                "most natural messages possible. Ask smart bundled questions, never forms."
            ),
            model_type="main",
        )

        self.required_fields = REQUIRED_FIELDS

        # Priority for asking: destination first, vibe last (often inferable)
        self.field_priority = [
            "destinations",
            "duration_days",
            "num_travelers",
            "budget_range",
            "travel_vibe",
        ]

    async def run(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process user input and extract/request travel preferences.
        Returns assistant_message + updated preferences + phase info.
        """
        context = context or {}
        current_prefs = dict(context.get("preferences", {}) or {})
        conversation_history = context.get("conversation_history", [])
        missing_fields = list(context.get("missing_fields", []) or [])

        # ------------------------------------------------------------------
        # Inference pass 1: "surprise me" → destination_open
        # ------------------------------------------------------------------
        surprise_keywords = [
            "surprise me", "you decide", "you choose", "suggest a place",
            "pick a place", "you pick", "anywhere", "somewhere nice",
            "recommend a destination", "suggest me", "up to you",
            "no specific", "any place", "you suggest", "don't know where",
            "no idea", "not sure where",
        ]
        user_lower = user_input.lower()
        if any(kw in user_lower for kw in surprise_keywords):
            if not current_prefs.get("destinations"):
                current_prefs["destinations"] = ["agent_surprise"]
                current_prefs["destination_open"] = True

        # ------------------------------------------------------------------
        # Inference pass 2: mood pill → travel_vibe
        # ------------------------------------------------------------------
        if current_prefs.get("current_mood") and not current_prefs.get("travel_vibe"):
            current_prefs["travel_vibe"] = [current_prefs["current_mood"]]

        # ------------------------------------------------------------------
        # Compute which funnel phase we're in (deterministic)
        # ------------------------------------------------------------------
        phase = _compute_onboarding_phase(current_prefs)

        # If already in phase_4_ready, mark complete immediately (no LLM call needed)
        if phase == "phase_4_ready":
            return {
                "assistant_message": "",
                "preferences": current_prefs,
                "missing_fields": [],
                "is_complete": True,
                "onboarding_phase": phase,
                "response": "",
                "data": {"preferences": current_prefs, "missing_fields": []},
                "error": None,
            }

        # ------------------------------------------------------------------
        # Build what fields are still missing (for prompt context)
        # ------------------------------------------------------------------
        satisfied = {
            "destinations": bool(current_prefs.get("destinations"))
                            or current_prefs.get("destination_open"),
            "duration_days": current_prefs.get("duration_days") is not None,
            "num_travelers": current_prefs.get("num_travelers") is not None,
            "budget_range": bool(current_prefs.get("budget_range")),
            "travel_vibe": bool(current_prefs.get("travel_vibe")),
        }
        effective_missing = [f for f in self.required_fields if not satisfied.get(f, False)]

        # ------------------------------------------------------------------
        # Build prompt
        # ------------------------------------------------------------------
        extraction_prompt = self._build_extraction_prompt(
            user_input=user_input,
            current_prefs=current_prefs,
            conversation_history=conversation_history,
            effective_missing=effective_missing,
            phase=phase,
        )

        schema = {
            "type": "object",
            "properties": {
                "assistant_message": {"type": "string"},
                "onboarding_phase": {"type": "string"},
                "destination_suggestions": {
                    "type": "array",
                    "description": "Only populated in phase_2_suggestions. 3 destination cards.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string"},
                            "emoji": {"type": "string"},
                            "pitch": {"type": "string"},
                            "best_for": {"type": "string"},
                        },
                        "required": ["city", "emoji", "pitch"],
                    },
                },
                "preferences": {
                    "type": "object",
                    "properties": {
                        "destinations": {"type": "array", "items": {"type": "string"}},
                        "destination_open": {"type": "boolean"},
                        "origin_city": {"type": "string"},
                        "duration_days": {"type": "integer"},
                        "start_date": {"type": "string"},
                        "end_date": {"type": "string"},
                        "num_travelers": {"type": "integer"},
                        "budget_range": {"type": "string"},
                        "travel_vibe": {"type": "array", "items": {"type": "string"}},
                        "pace": {"type": "string"},
                        "travel_style": {"type": "string"},
                        "trip_motivation": {"type": "string"},
                        "spontaneity": {"type": "string"},
                        "special_requirements": {"type": "string"},
                        "interests": {"type": "array", "items": {"type": "string"}},
                        "city_segments": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "city": {"type": "string"},
                                    "days": {"type": "integer"},
                                    "vibe": {"type": "array", "items": {"type": "string"}},
                                    "arrives_from": {"type": "string"},
                                    "transport_preference": {"type": "string"},
                                },
                                "required": ["city", "days"],
                            },
                        },
                    },
                },
                "is_complete": {"type": "boolean"},
                "missing_fields": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["assistant_message", "preferences", "is_complete", "missing_fields", "onboarding_phase"],
        }

        result = await self.generate_structured(extraction_prompt, schema)

        if result:
            extracted = result.get("preferences", {}) or {}
            extracted = {k: v for k, v in extracted.items() if v is not None}
            merged = {**current_prefs, **extracted}

            # Re-compute missing deterministically (don't trust LLM's missing_fields alone)
            computed_missing = [
                f for f in self.required_fields
                if not merged.get(f)
                and not (f == "destinations" and merged.get("destination_open"))
            ]
            is_complete = len(computed_missing) == 0

            result_phase = result.get("onboarding_phase", phase)
            destination_suggestions = result.get("destination_suggestions") or []

            return {
                "assistant_message": result.get("assistant_message", ""),
                "preferences": merged,
                "missing_fields": computed_missing,
                "is_complete": is_complete,
                "onboarding_phase": result_phase,
                "destination_suggestions": destination_suggestions,
                # Standardized output for Supervisor
                "response": result.get("assistant_message", ""),
                "data": {
                    "preferences": merged,
                    "missing_fields": computed_missing,
                    "destination_suggestions": destination_suggestions,
                },
                "error": None,
            }

        # ------------------------------------------------------------------
        # Fallback — should rarely happen (LLM call failed)
        # ------------------------------------------------------------------
        return {
            "assistant_message": (
                "Hey! Let's plan your perfect trip 🗺️\n\n"
                "Quick question to get started — where are you thinking of going, "
                "and how long do you have?\n\n"
                "📍 I already have a destination in mind\n"
                "🌏 Suggest somewhere for me\n"
                "🏙️ I want a multi-city adventure"
            ),
            "preferences": current_prefs,
            "missing_fields": self.required_fields,
            "is_complete": False,
            "onboarding_phase": "phase_1_intake",
            "destination_suggestions": [],
            "response": "Let's figure out your trip!",
            "data": {},
            "error": "Failed to generate structured response",
        }

    def _build_extraction_prompt(
        self,
        user_input: str,
        current_prefs: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, Any]]],
        effective_missing: List[str],
        phase: str,
    ) -> str:
        """Build the phase-aware extraction prompt."""
        history_text = ""
        if conversation_history:
            recent = conversation_history[-20:]  # Reduced from 50 — keep prompt lean
            history_lines = []
            for msg in recent:
                role = msg.get("role", "user").upper()
                content = msg.get("content", "")[:300]
                history_lines.append(f"{role}: {content}")
            history_text = "\n".join(history_lines)

        destinations = current_prefs.get("destinations", [])
        is_multi_city = isinstance(destinations, list) and len(destinations) > 1
        is_surprise = current_prefs.get("destination_open") or (
            isinstance(destinations, list) and "agent_surprise" in destinations
        )

        surprise_section = ""
        if is_surprise:
            surprise_section = """
<surprise_destination_mode>
The user wants YOU to pick a destination. Do NOT ask them again.
In phase_2_suggestions: provide 3 destination cards in destination_suggestions[].
Each card: city, emoji, one-line pitch (max 12 words), best_for tag.
Pick destinations that match their vibe/budget/duration if known.
Example: {"city": "Goa", "emoji": "🏖️", "pitch": "Beaches, feni, and sunsets that never disappoint", "best_for": "chill + nightlife"}
</surprise_destination_mode>
"""

        multi_city_section = ""
        if is_multi_city:
            multi_city_section = f"""
<multi_city_instructions>
User wants multiple cities: {', '.join(destinations)}.
Fill city_segments[] — one entry per city with city, days, vibe, arrives_from, transport_preference.
Propose a natural day split proactively. Once confirmed, set is_complete=true.
</multi_city_instructions>
"""

        return build_clarification_extraction_prompt(
            user_input=user_input,
            current_prefs=current_prefs,
            history_text=history_text,
            prioritized_missing=effective_missing,
            surprise_section=surprise_section,
            multi_city_section=multi_city_section,
            onboarding_phase=phase,
        )
