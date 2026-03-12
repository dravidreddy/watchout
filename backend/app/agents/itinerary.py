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
        
        macro_journey = await self._generate_macro_journey(preferences)
        macro_journey_context = ""
        if macro_journey:
            import json
            macro_journey_context = json.dumps(macro_journey)
            
        prompt = self._build_itinerary_prompt(preferences, places_data, weather_data, timezone_id, macro_journey_context)
        
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
                                        "latitude": {"type": "number"},
                                        "longitude": {"type": "number"},
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
                itinerary_obj = self._convert_to_itinerary(result, macro_journey)
                
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
        timezone_id: str = "UTC",
        macro_journey_context: str = ""
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
        trip_motivation = preferences.get("trip_motivation", "")
        spontaneity = preferences.get("spontaneity", "moderate")
        special_requirements = preferences.get("special_requirements", "none")

        # Bug 4 fix: extract origin city and transport preference so the LLM
        # knows what destinations are reachable and how the group is travelling.
        origin_city = preferences.get("origin_city", "")
        transport_preference = (
            preferences.get("transport")
            or preferences.get("transport_preference")
            or preferences.get("travel_style", "flexible")
        )

        # Bug 5 fix: derive a group-size-aware accommodation hint so the LLM
        # recommends villas/family rooms for groups rather than hostels/singles.
        if isinstance(num_travelers, int) and num_travelers >= 4:
            group_accommodation_hint = (
                f"Group of {num_travelers}: prefer villas, family rooms, or serviced apartments. "
                "Avoid hostels and single/double-bed rooms."
            )
        elif isinstance(num_travelers, int) and num_travelers == 2:
            group_accommodation_hint = "Couple: prioritise boutique hotels or romantic stays."
        elif isinstance(num_travelers, int) and num_travelers == 1:
            group_accommodation_hint = "Solo traveller: hostels, guesthouses, or budget hotels are fine."
        else:
            group_accommodation_hint = ""

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
            trip_motivation=trip_motivation,
            spontaneity=spontaneity,
            special_requirements=special_requirements,
            interests=interests,
            food_prefs=food_prefs,
            weather_context=weather_context,
            places_data=places_data,
            # Bug 4 additions:
            origin_city=origin_city,
            transport_preference=transport_preference,
            # Bug 5 addition:
            group_accommodation_hint=group_accommodation_hint,
            # Features addition: optionally include a high level macro journey plan
            macro_journey_context=macro_journey_context,
        )

    async def _generate_macro_journey(self, preferences: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        origin_city = preferences.get("origin_city")
        destinations = preferences.get("destinations", [])
        destination_city = destinations[0] if destinations else None
        days = preferences.get("duration_days", 3)
        vibe = preferences.get("travel_vibe", [])
        vibe_str = ", ".join(vibe) if isinstance(vibe, list) else str(vibe) if vibe else "leisure"
        pace = preferences.get("pace", "moderate")
        
        if not origin_city or not destination_city or origin_city.lower().strip() == destination_city.lower().strip():
            return None
            
        road_trip_pref = preferences.get("road_trip_preference", "").lower()
        if "direct" in road_trip_pref:
            return None
            
        # Ensure we only do this for driving/flexible trips where road trips make sense
        transport_preference = (
            preferences.get("transport")
            or preferences.get("transport_preference")
            or preferences.get("travel_style", "flexible")
        ).lower()
        
        if "flight" in transport_preference or "train" in transport_preference:
            return None
            
        from app.agents.route import RouteAgent
        route_agent = RouteAgent()
        
        try:
            pitstops = await route_agent.discover_route_pitstops(origin_city, destination_city)
        except Exception:
            pitstops = []
            
        from app.prompts import build_macro_journey_prompt
        prompt = build_macro_journey_prompt(
            origin_city=origin_city,
            destination_city=destination_city,
            days=days,
            vibe_str=vibe_str,
            pace=pace,
            potential_pitstops=pitstops
        )
        
        schema = {
            "type": "object",
            "properties": {
                "origin": {"type": "string"},
                "destination": {"type": "string"},
                "stops": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "city_name": {"type": "string"},
                            "nights": {"type": "integer"},
                            "reason": {"type": "string"}
                        }
                    }
                }
            }
        }
        
        journey = await self.generate_structured(prompt, schema)
        return journey
    
    def _convert_to_itinerary(self, raw_plan: Dict[str, Any], macro_journey: Optional[Dict[str, Any]] = None) -> Itinerary:
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
                    estimated_cost=activity.get("estimated_cost"),
                    latitude=activity.get("latitude"),
                    longitude=activity.get("longitude")
                ))
            
            day_plan = DayPlan(
                day_number=day_data.get("day_number", 1),
                city=day_data.get("city", ""),
                stops=stops,
                notes=day_data.get("notes")
            )
            days.append(day_plan)
            
        journey_route_obj = None
        if macro_journey:
            from app.models.trip import JourneyRoute, JourneyStop
            stops = macro_journey.get("stops", [])
            journey_stops = []
            for s in stops:
                journey_stops.append(JourneyStop(
                    city_name=s.get("city_name", ""),
                    nights=s.get("nights", 0),
                    reason=s.get("reason")
                ))
            journey_route_obj = JourneyRoute(
                origin=macro_journey.get("origin", ""),
                destination=macro_journey.get("destination", ""),
                stops=journey_stops
            )
        
        return Itinerary(
            journey_route=journey_route_obj,
            days=days,
            total_estimated_cost=raw_plan.get("total_estimated_budget"),
            highlights=raw_plan.get("highlights", [])
        )
    
    def _generate_summary(self, plan: Dict[str, Any]) -> str:
        """Generate a beautiful, soothing, well-structured canonical markdown summary of the trip plan."""
        title = plan.get("title", "Your Trip")
        raw_days = plan.get("days", [])
        days = raw_days if isinstance(raw_days, list) else []
        total_days = len(days) if days else int(plan.get("num_days") or 1)
        highlights = plan.get("highlights", [])
        total_budget = plan.get("total_estimated_budget")

        CATEGORY_ICONS = {
            "sightseeing": "🏛️", "nature": "🌿", "beach": "🏖️", "food": "🍽️",
            "adventure": "🧗", "culture": "🎭", "temple": "🛕", "shopping": "🛍️",
            "relaxation": "🧘", "nightlife": "🎶", "transport": "🚂", "other": "📍",
        }
        TIME_ICONS = {"morning": "🌅", "afternoon": "☀️", "evening": "🌙"}

        def get_icon(activity: dict) -> str:
            cat = str(activity.get("category") or "").lower()
            for key in CATEGORY_ICONS:
                if key in cat:
                    return CATEGORY_ICONS[key]
            return "📍"

        lines: List[str] = []

        # Canonical Header
        lines.append(f"# ✈️ {total_days}-Day {title}")
        if highlights:
            lines.append(f"> **Highlights:** {' · '.join(highlights[:4])}")
        lines.append("")
        lines.append("---")
        lines.append("")

        for idx, day in enumerate(days, start=1):
            if not isinstance(day, dict):
                continue
            day_number = day.get("day_number") or idx
            day_label = day.get("theme") or day.get("city") or f"Day {idx}"
            city = day.get("city", "")
            activities = day.get("activities") if isinstance(day.get("activities"), list) else []

            morning: List[str] = []
            afternoon: List[str] = []
            evening: List[str] = []
            day_budget = 0

            for activity in activities:
                if not isinstance(activity, dict):
                    continue
                name = str(activity.get("name") or "Activity").strip()
                icon = get_icon(activity)
                time_text = str(activity.get("time") or "").strip()
                desc = str(activity.get("description") or "").strip()
                tip = str(activity.get("tips") or "").strip()

                # Enforce Canonical Markdown layout for each activity
                entry = f"**{time_text}** | {icon} **{name}**" if time_text else f"{icon} **{name}**"
                if desc:
                    entry += f"  \\n   *{desc[:120]}*"
                if tip:
                    entry += f"  \\n   💡 **Tip:** {tip[:80]}"

                hour = None
                if ":" in time_text:
                    try:
                        hour = int(time_text.split(":")[0])
                    except Exception:
                        hour = None

                if hour is None:
                    afternoon.append(entry)
                elif hour < 12:
                    morning.append(entry)
                elif hour < 17:
                    afternoon.append(entry)
                else:
                    evening.append(entry)

                try:
                    day_budget += int(activity.get("estimated_cost") or 0)
                except Exception:
                    pass

            city_str = f" in {city}" if city else ""
            lines.append(f"## 📅 Day {day_number}{city_str} — *{day_label}*")
            lines.append("")

            # Render enforced time blocks
            for period, bucket in [("Morning", morning), ("Afternoon", afternoon), ("Evening", evening)]:
                if bucket:
                    lines.append(f"### {TIME_ICONS[period.lower()]} {period}")
                    for item in bucket:
                        lines.append(f"- {item}")
                    lines.append("")

            # Render Meals canonically
            meals = day.get("meals", [])
            if meals and isinstance(meals, list):
                meal_lines = []
                for m in meals:
                    if isinstance(m, dict):
                        mtype = m.get("type", "").capitalize()
                        sug = m.get("suggestion", "")
                        if mtype and sug:
                            meal_lines.append(f"- **{mtype}**: {sug}")
                if meal_lines:
                    lines.append(f"### 🍽️ Meals")
                    lines.extend(meal_lines)
                    lines.append("")

            if day_budget > 0:
                lines.append(f"**💰 Day Estimate:** ₹{max(day_budget, 0):,}")
                lines.append("")

            lines.append("---")
            lines.append("")

        if total_budget:
            lines.append(f"### 💳 Total Trip Estimate: ₹{int(total_budget):,}")
            lines.append("")
        lines.append("*Need to tweak anything? Just say the word — we'll make it perfect for you!* 🎒✨")

        return "\\n".join(lines).strip()
    
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

