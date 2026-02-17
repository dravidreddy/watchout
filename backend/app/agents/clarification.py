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
- Any specific interests or must-see places
- Food preferences (vegetarian, local cuisine, specific requirements)
- Pace preference (packed schedule vs relaxed)

Ask maximum 2-3 questions at a time. Be conversational and fun!""",
            model_type="main"  # Use main model for preference understanding
        )
        
        self.required_fields = [
            "destinations",
            "duration_days",
            "num_travelers",
            "budget_range",
            "travel_vibe"
        ]
    
    async def run(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process user input and extract/request travel preferences.
        
        Returns:
            response: Conversational response
            extracted: Any preferences extracted from the input
            is_complete: Whether we have enough info to start planning
            missing_fields: What info we still need
        """
        context = context or {}
        current_prefs = context.get("extracted_preferences", {})
        conversation_history = context.get("conversation_history", [])
        
        # Build extraction prompt with conversation history
        extraction_prompt = self._build_extraction_prompt(user_input, current_prefs, conversation_history)
        
        schema = {
            "type": "object",
            "properties": {
                "extracted": {
                    "type": "object",
                    "properties": {
                        "destinations": {"type": "array", "items": {"type": "string"}},
                        "origin_city": {"type": "string"},
                        "duration_days": {"type": "integer"},
                        "start_date": {"type": "string"},
                        "end_date": {"type": "string"},
                        "num_travelers": {"type": "integer"},
                        "traveler_type": {"type": "string"},
                        "budget_range": {"type": "string"},
                        "daily_budget": {"type": "integer"},
                        "travel_vibe": {"type": "array", "items": {"type": "string"}},
                        "interests": {"type": "array", "items": {"type": "string"}},
                        "food_preferences": {"type": "array", "items": {"type": "string"}},
                        "pace": {"type": "string"},
                        "transport_preferences": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "is_complete": {"type": "boolean"},
                "missing_fields": {"type": "array", "items": {"type": "string"}},
                "follow_up_questions": {"type": "array", "items": {"type": "string"}}
            }
        }
        
        result = await self.generate_structured(extraction_prompt, schema)
        
        if result:
            # Merge extracted preferences
            extracted = result.get("extracted", {})
            # Remove None values
            extracted = {k: v for k, v in extracted.items() if v is not None}
            merged = {**current_prefs, **extracted}
            
            # Generate conversational response
            response = await self._generate_response(
                user_input,
                merged,
                result.get("follow_up_questions", []),
                result.get("is_complete", False)
            )
            
            return {
                "response": response,
                "extracted_preferences": merged,
                "is_complete": result.get("is_complete", False),
                "missing_fields": result.get("missing_fields", [])
            }
        
        # Fallback to simple response
        async for text in self.stream(user_input, context):
            pass  # Just get the full response
        
        return {
            "response": "I'd love to help you plan your trip! Could you tell me where you'd like to go and for how long?",
            "extracted_preferences": current_prefs,
            "is_complete": False,
            "missing_fields": self.required_fields
        }
    
    def _build_extraction_prompt(
        self,
        user_input: str,
        current_prefs: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Build prompt for preference extraction."""
        # Format conversation history
        history_text = ""
        if conversation_history:
            recent = conversation_history[-6:]  # Last 6 messages for context
            history_lines = []
            for msg in recent:
                role = msg.get("role", "user").upper()
                content = msg.get("content", "")[:400]  # Truncate long messages
                history_lines.append(f"{role}: {content}")
            history_text = "\n".join(history_lines)
        
        return f"""Analyze this conversation about travel planning and extract/update preferences.

CONVERSATION HISTORY:
{history_text if history_text else "No previous conversation."}

CURRENT USER MESSAGE: "{user_input}"

PREVIOUSLY EXTRACTED PREFERENCES: {current_prefs}

IMPORTANT INSTRUCTIONS:
1. Pay close attention to the ENTIRE conversation history
2. If the user corrects or changes any preference (like destination, dates, number of travelers), UPDATE it
3. The user's latest message takes priority - if they say "Mangalore" not "Goa", use Mangalore
4. Extract any NEW travel preferences mentioned
5. Merge with existing preferences, replacing any that were corrected

Minimum required for planning: destinations, duration, number of travelers, budget level, and travel vibe.

If not complete, suggest 1-2 friendly follow-up questions to ask."""
    
    async def _generate_response(
        self,
        user_input: str,
        preferences: Dict[str, Any],
        questions: List[str],
        is_complete: bool
    ) -> str:
        """Generate a well-structured, formatted conversational response."""
        
        if is_complete:
            destinations = preferences.get("destinations", ["your destination"])
            days = preferences.get("duration_days", "your trip")
            dest_str = ', '.join(destinations) if isinstance(destinations, list) else destinations
            vibe = preferences.get('travel_vibe', ['flexible'])
            vibe_str = ', '.join(vibe) if isinstance(vibe, list) else vibe
            
            return f"""🎉 **Perfect! I have everything I need!**

---

### 📋 Your Trip Summary

| Detail | Your Choice |
|--------|-------------|
| **Destination** | {dest_str} |
| **Duration** | {days} days |
| **Travelers** | {preferences.get('num_travelers', 1)} |
| **Budget** | {preferences.get('budget_range', 'Not specified')} |
| **Style** | {vibe_str} |

---

✨ **Let me craft your perfect itinerary now!**"""
        
        # Build the main response acknowledging what we understood
        response_parts = []
        
        # Acknowledge what we know
        if preferences:
            response_parts.append("### ✅ **Got it!**\n")
            
            understood = []
            if preferences.get("destinations"):
                dests = preferences.get("destinations")
                dest_str = ', '.join(dests) if isinstance(dests, list) else dests
                understood.append(f"📍 **Destination:** {dest_str}")
            if preferences.get("origin_city"):
                understood.append(f"🏠 **From:** {preferences.get('origin_city')}")
            if preferences.get("duration_days"):
                understood.append(f"📅 **Duration:** {preferences.get('duration_days')} days")
            if preferences.get("num_travelers"):
                understood.append(f"👥 **Travelers:** {preferences.get('num_travelers')}")
            if preferences.get("budget_range") or preferences.get("daily_budget"):
                budget = preferences.get("budget_range") or f"₹{preferences.get('daily_budget')}/day"
                understood.append(f"💰 **Budget:** {budget}")
            if preferences.get("travel_vibe"):
                vibes = preferences.get("travel_vibe")
                vibe_str = ', '.join(vibes) if isinstance(vibes, list) else vibes
                understood.append(f"✨ **Vibe:** {vibe_str}")
            if preferences.get("interests"):
                interests = preferences.get("interests")
                interests_str = ', '.join(interests) if isinstance(interests, list) else interests
                understood.append(f"🎯 **Interests:** {interests_str}")
            
            if understood:
                response_parts.append("\n".join(understood))
        else:
            response_parts.append("🌟 **Sounds exciting!**")
        
        # Add questions section at the end if we have questions
        if questions:
            response_parts.append("\n\n---\n")
            response_parts.append("### ❓ **Quick Questions**\n")
            response_parts.append("*Just need a bit more info to plan the perfect trip:*\n")
            for i, q in enumerate(questions[:3], 1):
                response_parts.append(f"{i}. {q}")
        
        return "\n".join(response_parts)
    
    async def generate_initial_greeting(self) -> str:
        """Generate a friendly initial greeting."""
        return """Hey there, fellow traveler! 🌴✈️

I'm your AI travel buddy, and I'm super excited to help you plan an amazing trip!

Where are you dreaming of going? And how many days do you have for this adventure?"""
