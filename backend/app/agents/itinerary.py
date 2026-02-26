"""
Watchout Backend - Itinerary Planner Agent
"""
from typing import Dict, Any, Optional, List
from datetime import date, timedelta

from app.agents.base import BaseAgent
from app.models.trip import DayPlan, ActivityStop, Itinerary


class ItineraryAgent(BaseAgent):
    """
    Agent that creates detailed day-by-day itineraries.
    Synthesizes input from other agents into a cohesive plan.
    """
    
    def __init__(self):
        super().__init__(
            name="Itinerary Architect",
            description="""You create detailed, practical day-by-day travel itineraries for India.

Your responsibilities:
- Create realistic daily schedules with proper timing
- Balance activities with rest and travel time
- Consider the user's pace preferences (relaxed vs packed)
- Account for local factors (weather, opening hours, crowds)
- Include a mix of must-see attractions and hidden gems
- Suggest optimal order for visiting places
- Factor in meal times and food experiences

Output structured itineraries with specific times and durations.""",
            model_type="main"  # Use main model for complex itinerary generation
        )
    
    async def run(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete itinerary based on preferences and research.
        Returns standardized format: {response, data, error}
        """
        context = context or {}
        preferences = context.get("preferences", {})
        weather_data = context.get("weather_data", {})
        timezone_id = context.get("timezone_id", "UTC")
        
        prompt = self._build_itinerary_prompt(preferences, places_data, weather_data, timezone_id)
        
        schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "summary": {"type": "string"},
                "days": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "day_number": {"type": "integer"},
                            "theme": {"type": "string"},
                            "city": {"type": "string"},
                            "activities": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "time": {"type": "string"},
                                        "name": {"type": "string"},
                                        "description": {"type": "string"},
                                        "duration_minutes": {"type": "integer"},
                                        "category": {"type": "string"},
                                        "estimated_cost": {"type": "integer"},
                                        "tips": {"type": "string"}
                                    }
                                }
                            },
                            "meals": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "type": {"type": "string"},
                                        "suggestion": {"type": "string"},
                                        "cuisine": {"type": "string"}
                                    }
                                }
                            },
                            "notes": {"type": "string"}
                        }
                    }
                },
                "total_estimated_budget": {"type": "integer"},
                "highlights": {"type": "array", "items": {"type": "string"}},
                "packing_suggestions": {"type": "array", "items": {"type": "string"}}
            }
        }
        
        try:
            result = await self.generate_structured(prompt, schema)
            
            if result:
                # Convert to our model format (if needed for Pydantic/DB)
                itinerary_obj = self._convert_to_itinerary(result)
                
                return {
                    "response": self._generate_summary(result),
                    "data": {
                        "itinerary": itinerary_obj,  # This might need serialization if it's a Pydantic model
                        "raw_plan": result
                    },
                    "error": None
                }
            
            return {
                "response": "I'm having trouble creating the itinerary. Let me try again with simpler suggestions.",
                "data": {},
                "error": "Empty result from LLM"
            }

        except Exception as e:
            return {
                "response": "I encountered an error while building your itinerary.",
                "data": {},
                "error": str(e)
            }
    
    def _build_itinerary_prompt(
        self,
        preferences: Dict[str, Any],
        places_data: Dict[str, Any],
        weather_data: Dict[str, Any],
        timezone_id: str = "UTC"
    ) -> str:
        """Build the itinerary generation prompt."""
        destinations = preferences.get("destinations", [])
        destination_list = ", ".join(destinations) if destinations else "your destination"
        days = preferences.get("duration_days", 3)
        budget = preferences.get("budget_range", "mid_range")
        vibe = preferences.get("travel_vibe", [])
        vibe_str = ", ".join(vibe) if isinstance(vibe, list) else str(vibe) if vibe else "leisure"
        pace = preferences.get("pace", "moderate")
        food_prefs = preferences.get("food_preferences", [])
        interests = preferences.get("interests", [])
        num_travelers = preferences.get("num_travelers", 1)
        travel_style = preferences.get("travel_style", "")

        # Translate pace to concrete activity count guidance
        pace_guide = {
            "relaxed": "max 3 activities per day with long breaks and unhurried meals",
            "moderate": "4 activities per day with reasonable travel gaps between them",
            "packed": "5-6 activities per day, tightly optimised but still enjoyable"
        }.get(pace, "4 activities per day with reasonable breaks")

        weather_context = ""
        if weather_data:
            weather_context = f"\nWeather context for planning:\n{weather_data}\n"

        from datetime import datetime, timezone
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo(timezone_id)
        except Exception:
            tz = timezone.utc
        current_time_str = datetime.now(tz).strftime("%A, %Y-%m-%d %H:%M %Z")

        prompt = f"""You are Watchout's master itinerary architect — an Indian travel expert who has personally experienced every corner of the subcontinent. Build a {days}-day trip to {destination_list} for {num_travelers} traveler(s).

TRAVELER PROFILE:
- Current Local Time of user: {current_time_str}
- Budget: {budget} (budget = ₹800–2,500/night, mid-range = ₹2,500–8,000, luxury = ₹12,000+)
- Vibe: {vibe_str}
- Pace: {pace} → {pace_guide}
- Travel style: {travel_style or "unspecified"}
- Interests: {", ".join(interests) if interests else "general sightseeing"}
- Food preferences: {", ".join(food_prefs) if food_prefs else "open to everything"}
- Number of travelers: {num_travelers}
{weather_context}
ITINERARY DESIGN PRINCIPLES:

1. NARRATIVE ARC — Build a journey that unfolds like a great story:
   - Day 1: Orientation + the most iconic, unmissable highlight (they just arrived, buzzing with excitement — keep it manageable but thrilling, don't overwhelm)
   - Middle days: Deeper dives into local life — offbeat neighbourhoods, hidden temples, local markets, slower pace to savour the essence of the place
   - Final day: A genuinely memorable send-off (best sunset spot, the meal they'll talk about for years, easy logistics to airport/station)

2. EMBARGOED DESTINATIONS (EC3) — NEVER suggest travel to these regions under any circumstances:
   - Active conflict zones or areas requiring special inner-line permits that are currently suspended.
   - Sentinel Island (Strictly prohibited).
   - If the user explicitly asks for an embargoed region, gently redirect them to a safe alternative (e.g., redirect Sentinel Island to Havelock/Andaman).

3. VIBE-SPECIFIC CURATION — Let the vibe define the soul of every single day:
   - Romantic → private rooftop dinners, sunrise viewpoints, boutique cafés, avoid peak tourist crowds, include at least one special/intimate experience per day
   - Adventure → physical activities before 9 AM (Indian heat rises fast), rest/recovery in afternoons, local guide info for treks/rafting, flag gear needs
   - Cultural → heritage walks in the morning cool, museum visits, artisan markets, attend a local performance/festival if timing allows
   - Relaxed/Leisure → fewer spots with longer stays, a beach/garden/café break mid-day, deliberate "wander time" built into the schedule
   - Family → energy-managed pacing (kids tire quickly), 1 exciting + 1 relaxed activity per half-day, explicit snack/rest stop markers
   - Offbeat → avoid the top 3 tourist spots for at least 2 days; include a local neighbourhood walk, a chai stall interaction, a village/community experience

4. INDIA-SPECIFIC REALISM — These are non-negotiable:
   - Temple visits: explicitly note dress code (no shorts, cover shoulders, remove footwear), mention weekday vs weekend crowds
   - Rush hours 8–10 AM and 5–8 PM in all major cities — NEVER schedule inter-area travel during these windows
   - Indian mealtimes: breakfast 8–9:30 AM, lunch 1–2 PM (many places close between 3—6 PM), dinner 8–10 PM
   - Flag anywhere that requires advance booking (heritage hotel dinners, adventure activities, popular restaurants, monument tickets)
   - Monsoon months (Jul–Sep): flag outdoor activities that may be disrupted, always suggest a rain-friendly indoor alternative
   - Desert/Rajasthan: midday heat (11 AM–4 PM) is brutal — plan indoor/air-conditioned or shaded activities in this slot

4. HIDDEN GEMS — Every. Single. Day. must include at least one recommendation NOT on the standard tourist trail:
   A local street, a rooftop with a viewonly locals know, a family-run dhaba, a lesser-known temple or art gallery.
   Do not skip this — it's what separates a great itinerary from a guidebook.

6. REALISTIC TIMING — Be honest about time:
   - Never schedule more than 2 major sites before noon
   - Include actual travel time between spots (not just activity duration)
   - If a place requires 2+ hours of travel — build that into the day and reduce activities
   - Mark activities that require early starts (e.g., "Leave by 6 AM for the best sunrise at X")

7. CURRENCY FORMATTING (EC4) — Strict adherence required:
   - For INR, use the ₹ symbol and Indian numbering system (e.g., ₹1,50,000 NOT ₹150,000).
   - If quoting in non-INR currencies with 3 decimal places (e.g. KWD, OMR, BHD), you MUST preserve all three decimals (e.g., OMR 25.500).
"""

        if places_data:
            prompt += f"\nAvailable places data to incorporate:\n{places_data}\n"

        prompt += """
For every activity, provide:
- Specific clock time (e.g., "9:00 AM")
- Honest duration including walk/travel time to reach it
- Estimated cost in INR (range is fine: ₹200–₹500). Make sure to follow the EC4 formatting rules.
- One genuine local insider tip that most tourists miss

For every meal: name a SPECIFIC dish, not just "lunch". Example: "Kachori-sabzi at the local dhaba near the ghat" — not "have lunch somewhere".

Now build the complete, day-by-day itinerary. Make every day feel alive, personal, and expertly curated."""

        return prompt

    
    def _convert_to_itinerary(self, raw_plan: Dict[str, Any]) -> Itinerary:
        """Convert the raw plan to our Itinerary model."""
        days = []
        
        for day_data in raw_plan.get("days", []):
            stops = []
            
            for activity in day_data.get("activities", []):
                stops.append(ActivityStop(
                    name=activity.get("name", "Activity"),
                    description=activity.get("description"),
                    arrival_time=activity.get("time"),
                    duration_minutes=activity.get("duration_minutes", 60),
                    category=activity.get("category"),
                    estimated_cost=activity.get("estimated_cost")
                ))
            
            day_plan = DayPlan(
                day_number=day_data.get("day_number", 1),
                city=day_data.get("city", ""),
                stops=stops,
                notes=day_data.get("notes")
            )
            days.append(day_plan)
        
        return Itinerary(
            days=days,
            total_estimated_cost=raw_plan.get("total_estimated_budget"),
            highlights=raw_plan.get("highlights", [])
        )
    
    def _generate_summary(self, plan: Dict[str, Any]) -> str:
        """Generate a friendly summary of the itinerary."""
        title = plan.get("title", "Your Adventure")
        days = len(plan.get("days", []))
        highlights = plan.get("highlights", [])
        budget = plan.get("total_estimated_budget", 0)
        
        summary = f"""🗺️ **{title}**

I've crafted a {days}-day adventure for you!

**Highlights:**
"""
        
        for highlight in highlights[:5]:
            summary += f"✨ {highlight}\n"
        
        if budget:
            summary += f"\n💰 **Estimated Budget:** ₹{budget:,}"
        
        summary += "\n\nScroll down to see the detailed day-by-day plan!"
        
        return summary
    
    async def regenerate_day(
        self,
        day_number: int,
        current_plan: Dict[str, Any],
        feedback: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Regenerate a specific day based on feedback."""
        prompt = f"""The user wants to modify Day {day_number} of their itinerary.

Current Day {day_number} Plan:
{current_plan}

User Feedback: {feedback}

Generate an updated plan for Day {day_number} that addresses the feedback while maintaining a cohesive experience."""
        
        # Similar schema as above but for single day
        result = await self.generate_structured(prompt, {
            "type": "object",
            "properties": {
                "day_number": {"type": "integer"},
                "theme": {"type": "string"},
                "city": {"type": "string"},
                "activities": {"type": "array"},
                "meals": {"type": "array"},
                "notes": {"type": "string"}
            }
        })
        
        return result or {}
