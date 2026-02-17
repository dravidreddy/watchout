"""
Watchout Backend - Mapbox Directions API Tool
"""
import httpx
from typing import Optional, List, Dict, Any, Tuple

from app.core.config import settings


class MapboxTool:
    """MCP Tool wrapper for Mapbox APIs."""
    
    DIRECTIONS_URL = "https://api.mapbox.com/directions/v5/mapbox"
    GEOCODING_URL = "https://api.mapbox.com/geocoding/v5/mapbox.places"
    
    def __init__(self):
        self.access_token = settings.mapbox_access_token
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_directions(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        waypoints: Optional[List[Tuple[float, float]]] = None,
        profile: str = "driving"
    ) -> Optional[Dict[str, Any]]:
        """
        Get directions between two points.
        
        Args:
            origin: (longitude, latitude) tuple
            destination: (longitude, latitude) tuple
            waypoints: Optional list of intermediate (longitude, latitude) tuples
            profile: Routing profile - driving, walking, cycling, driving-traffic
        
        Returns:
            Route information including duration, distance, and geometry
        """
        # Build coordinates string
        coords = [origin]
        if waypoints:
            coords.extend(waypoints)
        coords.append(destination)
        
        coords_str = ";".join([f"{lon},{lat}" for lon, lat in coords])
        
        params = {
            "access_token": self.access_token,
            "geometries": "geojson",
            "overview": "full",
            "steps": "true",
            "annotations": "duration,distance"
        }
        
        try:
            response = await self.client.get(
                f"{self.DIRECTIONS_URL}/{profile}/{coords_str}",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != "Ok":
                return None
            
            routes = data.get("routes", [])
            if not routes:
                return None
            
            route = routes[0]
            
            return {
                "duration_seconds": route.get("duration"),
                "duration_minutes": round(route.get("duration", 0) / 60),
                "distance_meters": route.get("distance"),
                "distance_km": round(route.get("distance", 0) / 1000, 1),
                "geometry": route.get("geometry"),
                "steps": self._parse_steps(route.get("legs", []))
            }
            
        except Exception as e:
            print(f"Mapbox directions error: {e}")
            return None
    
    async def get_route_for_day(
        self,
        stops: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Get optimized route for a day's stops.
        
        Args:
            stops: List of stops with latitude and longitude
        
        Returns:
            Complete route with all legs
        """
        if len(stops) < 2:
            return None
        
        coordinates = [
            (stop.get("longitude"), stop.get("latitude"))
            for stop in stops
            if stop.get("longitude") and stop.get("latitude")
        ]
        
        if len(coordinates) < 2:
            return None
        
        # Build coordinates string
        coords_str = ";".join([f"{lon},{lat}" for lon, lat in coordinates])
        
        params = {
            "access_token": self.access_token,
            "geometries": "geojson",
            "overview": "full",
            "steps": "true"
        }
        
        try:
            response = await self.client.get(
                f"{self.DIRECTIONS_URL}/driving/{coords_str}",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != "Ok":
                return None
            
            routes = data.get("routes", [])
            if not routes:
                return None
            
            route = routes[0]
            legs = route.get("legs", [])
            
            return {
                "total_duration_minutes": round(route.get("duration", 0) / 60),
                "total_distance_km": round(route.get("distance", 0) / 1000, 1),
                "geometry": route.get("geometry"),
                "legs": [
                    {
                        "from": stops[i].get("name"),
                        "to": stops[i + 1].get("name"),
                        "duration_minutes": round(leg.get("duration", 0) / 60),
                        "distance_km": round(leg.get("distance", 0) / 1000, 1)
                    }
                    for i, leg in enumerate(legs)
                ]
            }
            
        except Exception as e:
            print(f"Mapbox route error: {e}")
            return None
    
    async def geocode(
        self,
        query: str,
        types: Optional[str] = None,
        country: str = "IN"
    ) -> List[Dict[str, Any]]:
        """
        Geocode an address to coordinates.
        
        Args:
            query: Address or place name
            types: Optional type filter (e.g., "place,address")
            country: Country code to bias results
        
        Returns:
            List of geocoding results
        """
        params = {
            "access_token": self.access_token,
            "country": country,
            "limit": 5
        }
        
        if types:
            params["types"] = types
        
        try:
            response = await self.client.get(
                f"{self.GEOCODING_URL}/{query}.json",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            features = data.get("features", [])
            
            return [
                {
                    "place_name": f.get("place_name"),
                    "longitude": f.get("center", [None, None])[0],
                    "latitude": f.get("center", [None, None])[1],
                    "type": f.get("place_type", [None])[0]
                }
                for f in features
            ]
            
        except Exception as e:
            print(f"Mapbox geocoding error: {e}")
            return []
    
    async def reverse_geocode(
        self,
        longitude: float,
        latitude: float
    ) -> Optional[Dict[str, Any]]:
        """
        Reverse geocode coordinates to address.
        
        Args:
            longitude: Longitude
            latitude: Latitude
        
        Returns:
            Address information
        """
        params = {
            "access_token": self.access_token,
            "limit": 1
        }
        
        try:
            response = await self.client.get(
                f"{self.GEOCODING_URL}/{longitude},{latitude}.json",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            features = data.get("features", [])
            if not features:
                return None
            
            feature = features[0]
            
            # Extract context (city, state, country)
            context = {}
            for ctx in feature.get("context", []):
                if ctx.get("id", "").startswith("place"):
                    context["city"] = ctx.get("text")
                elif ctx.get("id", "").startswith("region"):
                    context["state"] = ctx.get("text")
                elif ctx.get("id", "").startswith("country"):
                    context["country"] = ctx.get("text")
            
            return {
                "place_name": feature.get("place_name"),
                "address": feature.get("text"),
                **context
            }
            
        except Exception as e:
            print(f"Mapbox reverse geocoding error: {e}")
            return None
    
    def _parse_steps(self, legs: List[Dict]) -> List[Dict[str, Any]]:
        """Parse route steps into a simpler format."""
        all_steps = []
        for leg in legs:
            for step in leg.get("steps", []):
                all_steps.append({
                    "instruction": step.get("maneuver", {}).get("instruction"),
                    "duration_seconds": step.get("duration"),
                    "distance_meters": step.get("distance"),
                    "name": step.get("name")
                })
        return all_steps
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Singleton instance
_mapbox_tool: Optional[MapboxTool] = None


def get_mapbox_tool() -> MapboxTool:
    """Get or create the Mapbox tool instance."""
    global _mapbox_tool
    if _mapbox_tool is None:
        _mapbox_tool = MapboxTool()
    return _mapbox_tool
