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
        context = context or {}
        city = context.get("city", "")
        
        if not city:
            response_parts = []
            async for chunk in self.stream(f"Weather question: {user_input}"):
                response_parts.append(chunk)
            return {"response": "".join(response_parts), "weather": None}
        
        forecast = await self.weather.get_forecast(city)
        alerts = await self.weather.check_weather_alerts(city)
        
        return {
            "response": self._format_response(city, forecast, alerts),
            "weather": forecast,
            "alerts": alerts
        }
    
    async def get_weather_for_trip(self, cities: List[str]) -> List[Dict[str, Any]]:
        """Get weather for multiple trip destinations."""
        results = []
        for city in cities:
            forecast = await self.weather.get_forecast(city)
            if forecast:
                results.append({"city": city, "forecast": forecast})
        return results
    
    def _format_response(self, city: str, forecast: Optional[Dict], alerts: List) -> str:
        response = f"🌤️ **Weather: {city}**\n\n"
        
        if alerts:
            response += "⚠️ **Alerts:**\n"
            for alert in alerts[:2]:
                response += f"• {alert.get('headline', 'Weather alert')}\n"
            response += "\n"
        
        if forecast:
            current = forecast.get("current", {})
            response += f"**Now:** {current.get('temp_c')}°C - {current.get('condition')}\n"
            response += f"Humidity: {current.get('humidity')}% | Wind: {current.get('wind_kph')} km/h\n\n"
            
            response += "**Forecast:**\n"
            for day in forecast.get("forecast", [])[:3]:
                response += f"• {day.get('date')}: {day.get('min_temp_c')}°-{day.get('max_temp_c')}°C, {day.get('condition')}\n"
        
        return response
