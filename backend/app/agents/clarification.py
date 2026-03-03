"""
Watchout Backend - Clarification Agent
"""
from typing import Dict, Any, Optional, List

from app.agents.base import BaseAgent
from app.prompts import build_clarification_extraction_prompt


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

Ask one primary question at a time with clear options.
Use this rhythm: short context sentence, one clear question, numbered options, gentle CTA.
Be conversational, concise, and never robotic.""",
            model_type="main"  # Use main model for preference understanding
        )
        
        self.required_fields = [
            "destinations",
            "duration_days",
            "num_travelers",
            "budget_range",
            "travel_vibe"
        ]
        # Priority order - ask the most critical fields first; vibe is inferable and asked last
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

        # Detect "surprise me" / open destination intent
        # If the user is asking the AI to choose a destination, we should NOT
        # keep asking them for one. Mark destinations as "agent_surprise" so
        # the system knows to pick something and move forward.
        surprise_keywords = [
            "surprise me", "you decide", "you choose", "suggest a place",
            "pick a place", "you pick", "anywhere", "somewhere nice",
            "recommend a destination", "suggest me", "up to you",
            "no specific", "any place", "you suggest"
        ]
        user_lower = user_input.lower()
        if any(kw in user_lower for kw in surprise_keywords):
            if not current_prefs.get("destinations"):
                current_prefs["destinations"] = ["agent_surprise"]
                current_prefs["destination_open"] = True

        # Pre-fill travel_vibe from current_mood if not yet set
        # "current_mood" comes from the Home page mood pill (e.g. "spiritual").
        # We treat it as the seed for travel_vibe so the agent never asks again.
        if current_prefs.get("current_mood") and not current_prefs.get("travel_vibe"):
            current_prefs["travel_vibe"] = [current_prefs["current_mood"]]

        # Remove fields already satisfied in current_prefs
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
            # Merge extracted preferences - existing known prefs are never overwritten by None
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
            "assistant_message": (
                "To personalize this properly, I need one quick detail.\n"
                "Which destination should I plan first?\n"
                "1. I already have a city in mind\n"
                "2. Suggest a destination for me\n"
                "3. I want a multi-city route\n"
                "Reply with the option number, and I will take it from there."
            ),
            "preferences": current_prefs,
            "missing_fields": self.required_fields,
            "is_complete": False,
            "response": "What destination are you thinking about?",
            "data": {},
            "error": "Failed to generate structured response"
        }
    
    def _prioritize_missing_fields(self, missing_fields: list) -> list:
        """Return missing fields sorted by importance - destination first, vibe last."""
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
        is_surprise = current_prefs.get("destination_open") or (
            isinstance(destinations, list) and "agent_surprise" in destinations
        )

        surprise_section = ""
        if is_surprise:
            surprise_section = """
<surprise_destination_mode>
The user has asked YOU to choose a destination for them. Do NOT ask them again.
You MUST:
1. Pick a specific, wonderful destination that fits their vibe/budget/duration
2. Tell them why you chose it with genuine enthusiasm
3. Set destinations = ["<the city you picked>"] in the preferences output
4. Proceed as if they said "let's go to <city>"
Example: "Ooh, a surprise trip - my kind of request! Given your mid-range budget and love for beaches, 
I'm sending you to Goa! Perfect for a relaxed 3-day getaway..."
</surprise_destination_mode>
"""

        multi_city_section = ""
        if is_multi_city:
            multi_city_section = f"""
<multi_city_instructions>
The user wants to visit multiple cities: {', '.join(destinations)}.
You MUST fill city_segments[] in the preferences output - one entry per city with:
  - city: city name
  - days: days to spend there (propose a natural split if user hasn't specified)
  - vibe: activities/vibe for that city specifically
  - arrives_from: previous city or origin city
  - transport_preference: "flight" | "train" | "road" | "flexible"

Example day split guidance:
- Propose a split proactively: "10 days for Goa + Coorg + Mysore - how about 4 in Goa, 3 in Coorg, 3 in Mysore?"
- If user agrees, lock it in. If they adjust, update accordingly.
- Once all cities have days confirmed, set is_complete = true.
</multi_city_instructions>
"""

        return build_clarification_extraction_prompt(
            user_input=user_input,
            current_prefs=current_prefs,
            history_text=history_text,
            prioritized_missing=prioritized_missing,
            surprise_section=surprise_section,
            multi_city_section=multi_city_section,
        )

