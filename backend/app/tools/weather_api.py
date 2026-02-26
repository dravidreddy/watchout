"""
Watchout Backend - WeatherAPI Tool
"""
import httpx
from typing import Optional, List, Dict, Any
from datetime import date
import logging

logger = logging.getLogger(__name__)

from app.core.config import settings


class WeatherAPITool:
    """MCP Tool wrapper for WeatherAPI."""
    
    BASE_URL = "https://api.weatherapi.com/v1"
    
    def __init__(self):
        self.api_key = settings.weatherapi_key
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_current_weather(
        self,
        location: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get current weather for a location.
        
        Args:
            location: City name or coordinates
        
        Returns:
            Current weather data
        """
        params = {
            "key": self.api_key,
            "q": location,
            "aqi": "no"
        }
        
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/current.json",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            current = data.get("current", {})
            location_data = data.get("location", {})
            
            return {
                "location": location_data.get("name"),
                "region": location_data.get("region"),
                "country": location_data.get("country"),
                "temp_c": current.get("temp_c"),
                "temp_f": current.get("temp_f"),
                "feels_like_c": current.get("feelslike_c"),
                "condition": current.get("condition", {}).get("text"),
                "condition_icon": current.get("condition", {}).get("icon"),
                "humidity": current.get("humidity"),
                "wind_kph": current.get("wind_kph"),
                "wind_dir": current.get("wind_dir"),
                "uv": current.get("uv"),
                "is_day": current.get("is_day") == 1
            }
            
        except Exception as e:
            logger.warning("WeatherAPI current error: %s", e)
            return None
    
    async def get_forecast(
        self,
        location: str,
        days: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        Get weather forecast for a location.
        
        Args:
            location: City name or coordinates
            days: Number of days (1-14, free tier supports 3)
        
        Returns:
            Weather forecast data
        """
        params = {
            "key": self.api_key,
            "q": location,
            "days": min(days, 3),  # Free tier limit
            "aqi": "no",
            "alerts": "yes"
        }
        
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/forecast.json",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            forecast_days = data.get("forecast", {}).get("forecastday", [])
            alerts = data.get("alerts", {}).get("alert", [])
            
            return {
                "location": data.get("location", {}).get("name"),
                "current": self._parse_current(data.get("current", {})),
                "forecast": [
                    self._parse_forecast_day(day)
                    for day in forecast_days
                ],
                "alerts": [
                    {
                        "headline": alert.get("headline"),
                        "severity": alert.get("severity"),
                        "event": alert.get("event"),
                        "instruction": alert.get("instruction")
                    }
                    for alert in alerts
                ]
            }
            
        except Exception as e:
            logger.warning("WeatherAPI forecast error: %s", e)
            return None
    
    async def get_weather_for_trip(
        self,
        locations: List[str],
        start_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get weather for multiple trip locations.
        
        Args:
            locations: List of city names
            start_date: Optional trip start date
        
        Returns:
            Weather data for each location
        """
        results = []
        
        for location in locations:
            weather = await self.get_forecast(location)
            if weather:
                results.append({
                    "location": location,
                    "weather": weather
                })
        
        return results
    
    async def check_weather_alerts(
        self,
        location: str
    ) -> List[Dict[str, Any]]:
        """
        Check for weather alerts in a location.
        
        Args:
            location: City name or coordinates
        
        Returns:
            List of weather alerts
        """
        params = {
            "key": self.api_key,
            "q": location,
            "days": 1,
            "alerts": "yes"
        }
        
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/forecast.json",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            alerts = data.get("alerts", {}).get("alert", [])
            
            return [
                {
                    "headline": alert.get("headline"),
                    "severity": alert.get("severity"),
                    "event": alert.get("event"),
                    "areas": alert.get("areas"),
                    "effective": alert.get("effective"),
                    "expires": alert.get("expires"),
                    "instruction": alert.get("instruction")
                }
                for alert in alerts
            ]
            
        except Exception as e:
            logger.warning("WeatherAPI alerts error: %s", e)
            return []
    
    def _parse_current(self, current: Dict) -> Dict[str, Any]:
        """Parse current weather data."""
        return {
            "temp_c": current.get("temp_c"),
            "feels_like_c": current.get("feelslike_c"),
            "condition": current.get("condition", {}).get("text"),
            "condition_icon": current.get("condition", {}).get("icon"),
            "humidity": current.get("humidity"),
            "wind_kph": current.get("wind_kph")
        }
    
    def _parse_forecast_day(self, day: Dict) -> Dict[str, Any]:
        """Parse a single forecast day."""
        day_data = day.get("day", {})
        astro = day.get("astro", {})
        
        return {
            "date": day.get("date"),
            "max_temp_c": day_data.get("maxtemp_c"),
            "min_temp_c": day_data.get("mintemp_c"),
            "avg_temp_c": day_data.get("avgtemp_c"),
            "condition": day_data.get("condition", {}).get("text"),
            "condition_icon": day_data.get("condition", {}).get("icon"),
            "max_wind_kph": day_data.get("maxwind_kph"),
            "total_precip_mm": day_data.get("totalprecip_mm"),
            "avg_humidity": day_data.get("avghumidity"),
            "chance_of_rain": day_data.get("daily_chance_of_rain"),
            "uv": day_data.get("uv"),
            "sunrise": astro.get("sunrise"),
            "sunset": astro.get("sunset"),
            "is_good_for_outdoor": self._is_good_weather(day_data)
        }
    
    def _is_good_weather(self, day_data: Dict) -> bool:
        """Determine if weather is good for outdoor activities."""
        rain_chance = day_data.get("daily_chance_of_rain", 0)
        max_wind = day_data.get("maxwind_kph", 0)
        precip = day_data.get("totalprecip_mm", 0)
        
        return rain_chance < 50 and max_wind < 40 and precip < 5
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Singleton instance
_weather_tool: Optional[WeatherAPITool] = None


def get_weather_tool() -> WeatherAPITool:
    """Get or create the WeatherAPI tool instance."""
    global _weather_tool
    if _weather_tool is None:
        _weather_tool = WeatherAPITool()
    return _weather_tool
