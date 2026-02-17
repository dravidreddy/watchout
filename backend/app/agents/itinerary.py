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
        """
        context = context or {}
        preferences = context.get("preferences", {})
        places_data = context.get("places_data", {})
        weather_data = context.get("weather_data", {})
        
        prompt = self._build_itinerary_prompt(preferences, places_data, weather_data)
        
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
        
        result = await self.generate_structured(prompt, schema)
        
        if result:
            # Convert to our model format
            itinerary = self._convert_to_itinerary(result)
            
            return {
                "response": self._generate_summary(result),
                "itinerary": itinerary,
                "raw_plan": result
            }
        
        return {
            "response": "I'm having trouble creating the itinerary. Let me try again with simpler suggestions.",
            "itinerary": None,
            "raw_plan": None
        }
    
    def _build_itinerary_prompt(
        self,
        preferences: Dict[str, Any],
        places_data: Dict[str, Any],
        weather_data: Dict[str, Any]
    ) -> str:
        """Build the itinerary generation prompt."""
        destinations = preferences.get("destinations", [])
        days = preferences.get("duration_days", 3)
        budget = preferences.get("budget_range", "mid_range")
        vibe = preferences.get("travel_vibe", ["adventure"])
        pace = preferences.get("pace", "moderate")
        food_prefs = preferences.get("food_preferences", [])
        interests = preferences.get("interests", [])
        
        prompt = f"""Create a detailed {days}-day itinerary for {', '.join(destinations)}.

TRAVELER PREFERENCES:
- Budget Level: {budget}
- Travel Vibe: {', '.join(vibe) if isinstance(vibe, list) else vibe}
- Pace: {pace}
- Food Preferences: {', '.join(food_prefs) if food_prefs else 'No restrictions'}
- Special Interests: {', '.join(interests) if interests else 'General sightseeing'}
- Number of Travelers: {preferences.get('num_travelers', 1)}

"""
        
        if places_data:
            prompt += f"""
AVAILABLE PLACES DATA:
{places_data}
"""
        
        if weather_data:
            prompt += f"""
WEATHER FORECAST:
{weather_data}
"""
        
        prompt += """
Create a realistic, enjoyable itinerary with:
1. Specific times for each activity (e.g., "9:00 AM")
2. Realistic durations including travel between spots
3. A good balance of activities and rest
4. Local food recommendations for each meal
5. Budget estimates in INR
6. Pro tips for each major activity

Make it feel like advice from a friend who knows the place well!"""
        
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
