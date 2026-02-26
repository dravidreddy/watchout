"""
Watchout Backend - Weather Agent
"""
from typing import Dict, Any, Optional, List
from app.agents.base import BaseAgent
from app.tools.weather_api import get_weather_tool


class WeatherAgent(BaseAgent):
    """Agent that provides weather forecasts and travel advisories."""
    
    def __init__(self):
        super().__init__(
            name="Weather Advisor",
            description="You provide weather forecasts and seasonal advice for India travel."
        )
        self.weather = get_weather_tool()
    
    async def run(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get weather for a city.
        Returns standardized format: {response, data, error}
        """
        context = context or {}
        preferences = context.get("preferences", {})
        
        cities = preferences.get("destinations", [])
        if not cities and context.get("city"):
            cities = [context.get("city")]
            
        if not cities:
            response_parts = []
            async for chunk in self.stream(
                f"""You are Watchout, India's warmest travel companion. Answer this weather or seasons question.

Question: {user_input}

Be specific about Indian seasons, regional variation, and practical advice (what to pack, what to expect, what to avoid)."""
            ):
                response_parts.append(chunk)

            return {
                "response": "".join(response_parts),
                "data": {"weather": None},
                "error": None
            }
        
        try:
            all_forecasts = []
            all_alerts = []
            responses = []
            
            for city in cities[:3]:  # Limit to 3 cities to avoid slow API calls
                forecast = await self.weather.get_forecast(city)
                alerts = await self.weather.check_weather_alerts(city)
                
                if forecast:
                    all_forecasts.append({"city": city, "forecast": forecast})
                if alerts:
                    all_alerts.extend(alerts)
                    
                # Combine narrative responses for multiple cities if needed, 
                # but it's simpler to just generate one consolidated narrative.
            
            # Use LLM to generate one narrative for all cities
            response = await self._format_narrative_response(", ".join(cities[:3]), all_forecasts, all_alerts, preferences)

            return {
                "response": response,
                "data": {
                    "weather": all_forecasts,
                    "alerts": all_alerts
                },
                "error": None
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "response": "I couldn't fetch the weather right now.",
                "data": {},
                "error": str(e)
            }
    
    async def get_weather_for_trip(self, cities: List[str]) -> List[Dict[str, Any]]:
        """Get weather for multiple trip destinations."""
        results = []
        for city in cities:
            forecast = await self.weather.get_forecast(city)
            if forecast:
                results.append({"city": city, "forecast": forecast})
        return results
    
    async def _format_narrative_response(
        self,
        city: str,
        forecast: Optional[Dict],
        alerts: List,
        preferences: Optional[Dict] = None
    ) -> str:
        """Use LLM to generate a human, travel-focused weather briefing."""
        preferences = preferences or {}
        vibe = preferences.get("travel_vibe", [])
        vibe_str = ", ".join(vibe) if isinstance(vibe, list) else str(vibe) if vibe else "general travel"
        trip_dates = preferences.get("start_date", "upcoming trip")

        prompt = f"""You are Watchout's weather advisor — a practical, warm Indian travel companion.

City: {city}
Forecast data: {forecast}
Weather alerts: {alerts}
Traveler vibe: {vibe_str}
Trip dates: {trip_dates}

Write a 3–5 sentence weather briefing for this traveler. Make it genuinely useful:
1. What's the weather actually LIKE (not just numbers — "pleasantly warm" vs "uncomfortably humid" vs "surprisingly cold once the sun sets")
2. How does this affect their specific trip activities? (Beach day? Trekking? City sightseeing? Adjust per their vibe)
3. What to PACK based on this forecast (one specific recommendation: "bring a light cardigan for evenings" or "rain jacket is essential, not optional")
4. If there are alerts, explain what they MEAN for a traveler, not just repeat the technical text
5. Any seasonal local tip (e.g., "Holi weekend means street colours everywhere — wear clothes you don't mind staining")

Tone: warm and conversational, like a friend who just checked the weather for you. Don't be robotic or clinical.
Keep it to 3–5 sentences max. No bullet points — flowing, natural prose."""

        response_parts = []
        async for chunk in self.stream(prompt):
            response_parts.append(chunk)

        result = "".join(response_parts)

        # Prepend any raw alerts as a brief visual cue if they exist
        if alerts:
            alert_text = "\n".join([f"⚠️ {a.get('headline', 'Weather alert')}" for a in alerts[:2]])
            return f"{alert_text}\n\n{result}"

        return result
