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
        
        Context should include:
        - stops: List of stops with coordinates
        - transport_mode: Preferred mode (driving, walking)
        """
        context = context or {}
        stops = context.get("stops", [])
        
        if len(stops) < 2:
            return {
                "response": "Need at least 2 stops to calculate a route.",
                "route": None
            }
        
        # Calculate route
        route = await self.mapbox.get_route_for_day(stops)
        
        if route:
            return {
                "response": self._format_route_response(route),
                "route": route,
                "total_travel_time": route.get("total_duration_minutes"),
                "total_distance": route.get("total_distance_km")
            }
        
        return {
            "response": "Could not calculate route. Please check the locations.",
            "route": None
        }
    
    async def calculate_route(
        self,
        origin: Dict[str, float],
        destination: Dict[str, float],
        waypoints: Optional[List[Dict[str, float]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate route between two points with optional waypoints.
        
        Args:
            origin: {latitude, longitude}
            destination: {latitude, longitude}
            waypoints: Optional list of intermediate points
        
        Returns:
            Route information
        """
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
        """
        Add route information between activities in a day plan.
        
        Args:
            day_plan: Day plan with activities
        
        Returns:
            Day plan with route information added
        """
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
        """
        Add coordinates to stops that don't have them.
        
        Args:
            stops: List of stops, some may have addresses only
        
        Returns:
            Stops with coordinates added
        """
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
        """Format route information as a response."""
        total_time = route.get("total_duration_minutes", 0)
        total_dist = route.get("total_distance_km", 0)
        legs = route.get("legs", [])
        
        response = f"""🗺️ **Route Overview**

**Total Travel Time:** {total_time} minutes
**Total Distance:** {total_dist} km

**Route Breakdown:**
"""
        
        for leg in legs:
            response += f"• {leg.get('from')} → {leg.get('to')}: "
            response += f"{leg.get('duration_minutes')} min ({leg.get('distance_km')} km)\n"
        
        return response
