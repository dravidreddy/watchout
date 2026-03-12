"""
Watchout Backend - Route Agent
"""
from typing import Dict, Any, Optional, List

from app.agents.base import BaseAgent
from app.tools.mapbox import get_mapbox_tool


class RouteAgent(BaseAgent):
    """
    Agent that handles routing and navigation using Mapbox.
    Calculates optimal routes between stops and provides directions.
    """
    
    def __init__(self):
        super().__init__(
            name="Route Navigator",
            description="""You optimize travel routes and calculate realistic travel times.
You use Mapbox for accurate routing in India, considering:
- Traffic patterns
- Road conditions
- Multiple transport modes
- Optimal stop ordering"""
        )
        self.mapbox = get_mapbox_tool()
    
    async def run(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate routes for a day's activities.
        Returns standardized format: {response, data, error}
        """
        context = context or {}
        stops = context.get("stops", [])
        
        if len(stops) < 2:
            return {
                "response": "Need at least 2 stops to calculate a route.",
                "data": {},
                "error": "Insufficient stops"
            }
        
        # Calculate route
        try:
            route = await self.mapbox.get_route_for_day(stops)
            
            if route:
                return {
                    "response": self._format_route_response(route),
                    "data": {
                        "route": route,
                        "total_travel_time": route.get("total_duration_minutes"),
                        "total_distance": route.get("total_distance_km")
                    },
                    "error": None
                }
            
            return {
                "response": "Could not calculate route. Please check the locations.",
                "data": {},
                "error": "Route calculation failed"
            }
        except Exception as e:
            return {
                "response": "An error occurred while calculating the route.",
                "data": {},
                "error": str(e)
            }

    # ... (Keep existing methods: calculate_route, add_routes_to_day_plan, geocode_stops) -> Can copy them or just let Python keep them if I was patching, but I am overwriting so I MUST provide them.
    
    async def calculate_route(
        self,
        origin: Dict[str, float],
        destination: Dict[str, float],
        waypoints: Optional[List[Dict[str, float]]] = None
    ) -> Optional[Dict[str, Any]]:
        """Calculate route between two points with optional waypoints."""
        origin_tuple = (origin["longitude"], origin["latitude"])
        dest_tuple = (destination["longitude"], destination["latitude"])
        
        waypoint_tuples = None
        if waypoints:
            waypoint_tuples = [
                (wp["longitude"], wp["latitude"]) for wp in waypoints
            ]
        
        route = await self.mapbox.get_directions(
            origin_tuple,
            dest_tuple,
            waypoint_tuples
        )
        
        return route
    
    async def add_routes_to_day_plan(
        self,
        day_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add route information between activities in a day plan."""
        activities = day_plan.get("activities", [])
        
        if len(activities) < 2:
            return day_plan
        
        # Build stops list with coordinates
        stops = []
        for activity in activities:
            if activity.get("latitude") and activity.get("longitude"):
                stops.append({
                    "name": activity.get("name"),
                    "latitude": activity.get("latitude"),
                    "longitude": activity.get("longitude")
                })
        
        if len(stops) < 2:
            return day_plan
        
        # Get route
        route = await self.mapbox.get_route_for_day(stops)
        
        if route:
            day_plan["route"] = route
            day_plan["travel_time_minutes"] = route.get("total_duration_minutes")
            
            # Add individual leg times
            legs = route.get("legs", [])
            for i, leg in enumerate(legs):
                if i < len(activities) - 1:
                    activities[i]["travel_to_next"] = {
                        "duration_minutes": leg.get("duration_minutes"),
                        "distance_km": leg.get("distance_km")
                    }
        
        return day_plan
    
    async def geocode_stops(
        self,
        stops: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Add coordinates to stops that don't have them."""
        updated_stops = []
        
        for stop in stops:
            if stop.get("latitude") and stop.get("longitude"):
                updated_stops.append(stop)
                continue
            
            # Try to geocode
            address = stop.get("address") or stop.get("name")
            city = stop.get("city", "")
            
            if address:
                query = f"{address} {city}".strip()
                results = await self.mapbox.geocode(query)
                
                if results:
                    stop["latitude"] = results[0].get("latitude")
                    stop["longitude"] = results[0].get("longitude")
            
            updated_stops.append(stop)
        
        return updated_stops
    
    def _format_route_response(self, route: Dict[str, Any]) -> str:
        """Format route information as a conversational response."""
        total_time = route.get("total_duration_minutes", 0)
        total_dist = route.get("total_distance_km", 0)
        legs = route.get("legs", [])
        
        # Convert total minutes to hours/mins for better readability
        hours = int(total_time // 60)
        mins = int(total_time % 60)
        time_str = f"{hours}h {mins}m" if hours > 0 else f"{mins} mins"
        
        response = f"I've mapped out the route! 🗺️ It covers about **{total_dist} km** and should take roughly **{time_str}** of driving time.\n\n"
        
        response += "**Here's the plan:**\n"
        for leg in legs:
            l_time = leg.get('duration_minutes')
            leg_time_str = f"{int(l_time // 60)}h {int(l_time % 60)}m" if l_time > 60 else f"{l_time} mins"
            response += f"• From **{leg.get('from')}** to **{leg.get('to')}**: ~{leg_time_str} ({leg.get('distance_km')} km)\n"
            
        return response

    async def discover_route_pitstops(
        self,
        origin_city: str,
        destination_city: str,
        country: str = "IN"
    ) -> List[Dict[str, Any]]:
        """
        Discover potential cities/pitstops between origin and destination.
        """
        # Geocode origin and destination
        origin_res = await self.mapbox.geocode(origin_city, types="place", country=country)
        dest_res = await self.mapbox.geocode(destination_city, types="place", country=country)
        
        if not origin_res or not dest_res:
            return []
            
        org = origin_res[0]
        dst = dest_res[0]
        
        # Calculate bounding box
        min_lon = min(org["longitude"], dst["longitude"])
        max_lon = max(org["longitude"], dst["longitude"])
        min_lat = min(org["latitude"], dst["latitude"])
        max_lat = max(org["latitude"], dst["latitude"])
        
        # Add a little padding (e.g., 0.5 degrees ~ 50km)
        padding = 0.5
        bbox = (min_lon - padding, min_lat - padding, max_lon + padding, max_lat + padding)
        
        cities = await self.mapbox.get_cities_in_bbox(bbox, country=country, limit=10)
        
        # Filter out origin and destination
        origin_name = org.get("name", "").lower()
        dest_name = dst.get("name", "").lower()
        
        valid_stops = []
        for city in cities:
            c_name = city.get("name", "").lower()
            if c_name and c_name not in origin_name and c_name not in dest_name:
                valid_stops.append(city)
                
        return valid_stops
