"""
Watchout Backend - Clarification Agent
"""
from typing import Dict, Any, Optional, List

from app.agents.base import BaseAgent


class ClarificationAgent(BaseAgent):
    """
    Agent that extracts travel preferences through friendly conversation.
    Asks smart, minimal questions to understand user needs.
    """
    
    def __init__(self):
        super().__init__(
            name="Travel Buddy",
            description="""You help travelers clarify their trip preferences through friendly conversation.
Your goal is to gather essential information without overwhelming the user.

Key information to gather:
- Destination(s) or type of trip desired
- Travel dates or duration
- Number of travelers and who they are (solo, couple, family, friends)
- Budget range (budget, mid-range, luxury)
- Travel vibe (adventure, relaxation, cultural, party, romantic)

Ask maximum 3 questions at a time. Be conversational and fun!""",
            model_type="main"  # Use main model for preference understanding
        )
        
        self.required_fields = [
            "destinations",
            "duration_days",
            "num_travelers",
            "budget_range",
            "travel_vibe"
        ]
        # Priority order — ask the most critical fields first; vibe is inferable and asked last
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
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process user input and extract/request travel preferences.
        """
        context = context or {}
        current_prefs = dict(context.get("preferences", {}) or {})
        conversation_history = context.get("conversation_history", [])
        missing_fields = list(context.get("missing_fields", []) or [])

        # ── Pre-fill travel_vibe from current_mood if not yet set ──────────
        # "current_mood" comes from the Home page mood pill (e.g. "spiritual").
        # We treat it as the seed for travel_vibe so the agent never asks again.
        if current_prefs.get("current_mood") and not current_prefs.get("travel_vibe"):
            current_prefs["travel_vibe"] = [current_prefs["current_mood"]]

        # ── Remove fields already satisfied in current_prefs ───────────────
        # This prevents the LLM from asking questions we already know the answer to.
        satisfied = {
            "travel_vibe": bool(current_prefs.get("travel_vibe")),
            "budget_range": bool(current_prefs.get("budget_range")),
            "destinations": bool(current_prefs.get("destinations")),
            "duration_days": current_prefs.get("duration_days") is not None,
            "num_travelers": current_prefs.get("num_travelers") is not None,
            "origin_city": bool(current_prefs.get("origin_city")),
            "pace": bool(current_prefs.get("pace")),
        }
        effective_missing = [
            f for f in (missing_fields or self.required_fields)
            if not satisfied.get(f, False)
        ]

        # Build extraction prompt with conversation history
        extraction_prompt = self._build_extraction_prompt(
            user_input, current_prefs, conversation_history, effective_missing
        )

        schema = {
            "type": "object",
            "properties": {
                "assistant_message": {"type": "string"},
                "preferences": {
                    "type": "object",
                    "properties": {
                        "destinations": {"type": "array", "items": {"type": "string"}},
                        "origin_city": {"type": "string"},
                        "duration_days": {"type": "integer"},
                        "start_date": {"type": "string"},
                        "end_date": {"type": "string"},
                        "num_travelers": {"type": "integer"},
                        "budget_range": {"type": "string"},
                        "travel_vibe": {"type": "array", "items": {"type": "string"}},
                        "pace": {"type": "string"},
                        "interests": {"type": "array", "items": {"type": "string"}},
                        "city_segments": {
                            "type": "array",
                            "description": "Per-city breakdown for multi-city trips. Fill this when user mentions multiple destinations.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "city": {"type": "string"},
                                    "days": {"type": "integer"},
                                    "vibe": {"type": "array", "items": {"type": "string"}},
                                    "arrives_from": {"type": "string"},
                                    "transport_preference": {"type": "string"}
                                },
                                "required": ["city", "days"]
                            }
                        }
                    }
                },
                "is_complete": {"type": "boolean"},
                "missing_fields": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["assistant_message", "preferences", "is_complete", "missing_fields"]
        }

        result = await self.generate_structured(extraction_prompt, schema)

        if result:
            # Merge extracted preferences — existing known prefs are never overwritten by None
            extracted = result.get("preferences", {}) or {}
            extracted = {k: v for k, v in extracted.items() if v is not None}
            merged = {**current_prefs, **extracted}

            # Re-compute missing based on what's now in merged (not just what the LLM said)
            computed_missing = [
                f for f in self.required_fields
                if not merged.get(f)
            ]

            return {
                "assistant_message": result.get("assistant_message", ""),
                "preferences": merged,
                "missing_fields": computed_missing,
                "is_complete": len(computed_missing) == 0,

                # Standardized output for Supervisor
                "response": result.get("assistant_message", ""),
                "data": {
                    "preferences": merged,
                    "missing_fields": computed_missing
                },
                "error": None
            }

        # Fallback
        return {
            "assistant_message": "I'd love to help you plan your trip! Could you tell me where you'd like to go and for how long?",
            "preferences": current_prefs,
            "missing_fields": self.required_fields,
            "is_complete": False,
            "response": "Could you tell me where you'd like to go?",
            "data": {},
            "error": "Failed to generate structured response"
        }
    
    def _prioritize_missing_fields(self, missing_fields: list) -> list:
        """Return missing fields sorted by importance — destination first, vibe last."""
        ordered = [f for f in self.field_priority if f in missing_fields]
        others = [f for f in missing_fields if f not in self.field_priority]
        return ordered + others

    def _build_extraction_prompt(
        self,
        user_input: str,
        current_prefs: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        missing_fields: Optional[List[str]] = None
    ) -> str:
        """Build prompt for preference extraction."""
        history_text = ""
        if conversation_history:
            recent = conversation_history[-50:]
            history_lines = []
            for msg in recent:
                role = msg.get("role", "user").upper()
                content = msg.get("content", "")[:400]
                history_lines.append(f"{role}: {content}")
            history_text = "\n".join(history_lines)

        prioritized_missing = self._prioritize_missing_fields(missing_fields or self.required_fields)
        destinations = current_prefs.get("destinations", [])
        is_multi_city = isinstance(destinations, list) and len(destinations) > 1

        multi_city_section = ""
        if is_multi_city:
            multi_city_section = f"""
<multi_city_instructions>
The user wants to visit multiple cities: {', '.join(destinations)}.
You MUST fill city_segments[] in the preferences output — one entry per city with:
  - city: city name
  - days: days to spend there (propose a natural split if user hasn't specified)
  - vibe: activities/vibe for that city specifically
  - arrives_from: previous city or origin city
  - transport_preference: "flight" | "train" | "road" | "flexible"

Example day split guidance:
- Propose a split proactively: "10 days for Goa + Coorg + Mysore — how about 4 in Goa, 3 in Coorg, 3 in Mysore?"
- If user agrees, lock it in. If they adjust, update accordingly.
- Once all cities have days confirmed, set is_complete = true.
</multi_city_instructions>
"""

        return f"""<role>
You are "Watchout" — a warm, curious Indian travel consultant having a natural conversation with a traveler.
Your goal: understand what this person wants through genuine dialogue, NOT an interview or interrogation.
</role>

<what_you_know_already>
Full conversation so far:
{history_text}

User just said: "{user_input}"

Already captured from this conversation:
{current_prefs}

Fields still needed (highest priority listed first):
{prioritized_missing}
</what_you_know_already>
{multi_city_section}
<how_to_respond>
STEP 1 — EXTRACT DEEPLY:
Read the ENTIRE conversation above. Update 'preferences' with anything the user mentioned, even indirectly:
- "my wife and I" → num_travelers = 2, travel_style = "couple"
- "I hate crowded tourist spots" → travel_vibe = ["offbeat"], interests = ["peace", "nature"]
- "around Christmas" → infer start_date range (late December)
- "tight on budget" or "we're not doing luxury" → budget_range = "budget"
- "beach holiday", "chill trip", "relaxed" → pace = "relaxed", travel_vibe = ["leisure", "beach"]
- "adventure", "trekking", "outdoors" → travel_vibe = ["adventure"]
- "romantic getaway" → travel_vibe = ["romantic"]
Never ignore these signals just because they weren't in a formal field.

STEP 2 — ASSESS WHAT'S TRULY MISSING:
After extracting from the full conversation, what is GENUINELY still unknown and cannot be inferred?
Priority: destination (most critical) → duration → number of travelers → budget → vibe (can usually be inferred)
For multi-city trips: also need per-city day splits in city_segments[].
If vibe can be inferred from their language, do NOT ask for it.

STEP 3 — WRITE A WARM RESPONSE:
- Ask for at most 2 things at a time, and ONLY things that are truly critical and unknown
- Acknowledge what they've told you before asking more: "A week in Rajasthan for two — amazing choice! 🧡"
- Frame questions as genuine curiosity, not form fields
- If you have EVERYTHING needed, say so warmly and tell them you're ready to start planning
- NEVER ask for something the user already answered earlier in the conversation

STEP 4 — OUTPUT:
Return strict JSON only with keys: assistant_message, preferences, missing_fields, is_complete
</how_to_respond>
"""
