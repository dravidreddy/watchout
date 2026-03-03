"""
Watchout Backend - Itinerary Planner Agent
"""
from typing import Dict, Any, Optional, List
from datetime import date, timedelta

from app.agents.base import BaseAgent
from app.models.trip import DayPlan, ActivityStop, Itinerary
from app.prompts import build_itinerary_prompt, build_route_regeneration_prompt


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
        places_data = context.get("places_data", {})
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

        return build_itinerary_prompt(
            days=days,
            destination_list=destination_list,
            num_travelers=num_travelers,
            current_time_str=current_time_str,
            budget=budget,
            vibe_str=vibe_str,
            pace=pace,
            pace_guide=pace_guide,
            travel_style=travel_style,
            interests=interests,
            food_prefs=food_prefs,
            weather_context=weather_context,
            places_data=places_data,
        )

    
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
        """Generate premium markdown summary in a stable day-by-day format."""
        title = plan.get("title", "Trip Plan")
        raw_days = plan.get("days", [])
        days = raw_days if isinstance(raw_days, list) else []
        total_days = len(days) if days else int(plan.get("num_days") or 1)

        lines = [f"# ✈️ {total_days}-Day {title} Itinerary", ""]

        for idx, day in enumerate(days, start=1):
            if not isinstance(day, dict):
                continue
            day_number = day.get("day_number") or idx
            day_label = day.get("theme") or day.get("city") or "Highlights"
            activities = day.get("activities") if isinstance(day.get("activities"), list) else []

            morning: List[str] = []
            afternoon: List[str] = []
            evening: List[str] = []
            day_budget = 0

            for activity in activities:
                if not isinstance(activity, dict):
                    continue
                name = str(activity.get("name") or "Activity").strip()
                time_text = str(activity.get("time") or "").strip()
                hour = None
                if ":" in time_text:
                    try:
                        hour = int(time_text.split(":")[0])
                    except Exception:
                        hour = None
                if hour is None:
                    bucket = "afternoon"
                elif hour < 12:
                    bucket = "morning"
                elif hour < 17:
                    bucket = "afternoon"
                else:
                    bucket = "evening"

                if bucket == "morning":
                    morning.append(name)
                elif bucket == "evening":
                    evening.append(name)
                else:
                    afternoon.append(name)

                try:
                    day_budget += int(activity.get("estimated_cost") or 0)
                except Exception:
                    pass

            lines.append(f"## Day {day_number} - {day_label}")
            lines.append(f"- Morning: {', '.join(morning) if morning else 'Easy local start'}")
            lines.append(f"- Afternoon: {', '.join(afternoon) if afternoon else 'Core sightseeing'}")
            lines.append(f"- Evening: {', '.join(evening) if evening else 'Dinner and downtime'}")
            lines.append(f"- Budget estimate: INR {max(day_budget, 0):,}")
            lines.append("- Stay suggestion: Near the main day activities for easy transfers")
            lines.append("")

        total_budget = plan.get("total_estimated_budget")
        if total_budget:
            lines.append(f"**Trip budget estimate:** INR {int(total_budget):,}")

        return "\n".join(lines).strip()
    
    async def regenerate_day(
        self,
        day_number: int,
        current_plan: Dict[str, Any],
        feedback: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Regenerate a specific day based on feedback."""
        prompt = build_route_regeneration_prompt(
            day_number=day_number,
            current_plan=current_plan,
            feedback=feedback,
        )
        
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

