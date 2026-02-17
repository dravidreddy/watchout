"""
Watchout Backend - Google Places API Tool
"""
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.core.config import settings
from app.db.mongo import places_cache_collection


class GooglePlacesTool:
    """MCP Tool wrapper for Google Places API."""
    
    BASE_URL = "https://maps.googleapis.com/maps/api/place"
    
    def __init__(self):
        self.api_key = settings.google_places_api_key
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def search_places(
        self,
        query: str,
        location: Optional[str] = None,
        radius: int = 5000,
        place_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for places using Google Places Text Search.
        
        Args:
            query: Search query (e.g., "restaurants in Goa")
            location: Optional lat,lng string
            radius: Search radius in meters
            place_type: Optional place type filter
        
        Returns:
            List of place results
        """
        params = {
            "query": query,
            "key": self.api_key
        }
        
        if location:
            params["location"] = location
            params["radius"] = radius
        
        if place_type:
            params["type"] = place_type
        
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/textsearch/json",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "OK":
                return []
            
            return self._parse_results(data.get("results", []))
            
        except Exception as e:
            print(f"Google Places search error: {e}")
            return []
    
    async def search_nearby(
        self,
        latitude: float,
        longitude: float,
        radius: int = 1500,
        place_type: str = "tourist_attraction",
        keyword: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for nearby places.
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius: Search radius in meters
            place_type: Type of places to search
            keyword: Optional keyword filter
        
        Returns:
            List of nearby places
        """
        params = {
            "location": f"{latitude},{longitude}",
            "radius": radius,
            "type": place_type,
            "key": self.api_key
        }
        
        if keyword:
            params["keyword"] = keyword
        
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/nearbysearch/json",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "OK":
                return []
            
            return self._parse_results(data.get("results", []))
            
        except Exception as e:
            print(f"Google Places nearby search error: {e}")
            return []
    
    async def get_place_details(
        self,
        place_id: str,
        fields: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a place.
        
        Args:
            place_id: Google Place ID
            fields: Optional list of fields to include
        
        Returns:
            Place details or None
        """
        # Check cache first
        cache = places_cache_collection()
        cached = await cache.find_one({"place_id": place_id})
        if cached:
            return cached.get("details")
        
        # Default fields for cost optimization
        if fields is None:
            fields = [
                "name", "formatted_address", "formatted_phone_number",
                "geometry", "opening_hours", "photos", "rating",
                "reviews", "website", "url", "price_level", "types"
            ]
        
        params = {
            "place_id": place_id,
            "fields": ",".join(fields),
            "key": self.api_key
        }
        
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/details/json",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "OK":
                return None
            
            result = data.get("result", {})
            parsed = self._parse_place_details(result)
            
            # Cache the result
            await cache.insert_one({
                "place_id": place_id,
                "details": parsed,
                "cached_at": datetime.utcnow()
            })
            
            return parsed
            
        except Exception as e:
            print(f"Google Places details error: {e}")
            return None
    
    async def autocomplete(
        self,
        input_text: str,
        types: Optional[str] = None,
        location: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Get place autocomplete suggestions.
        
        Args:
            input_text: Partial text input
            types: Optional type filter (e.g., "(cities)")
            location: Optional bias location
        
        Returns:
            List of autocomplete predictions
        """
        params = {
            "input": input_text,
            "key": self.api_key
        }
        
        if types:
            params["types"] = types
        
        if location:
            params["location"] = location
            params["radius"] = 50000
        
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/autocomplete/json",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "OK":
                return []
            
            return [
                {
                    "place_id": pred.get("place_id"),
                    "description": pred.get("description"),
                    "main_text": pred.get("structured_formatting", {}).get("main_text"),
                    "secondary_text": pred.get("structured_formatting", {}).get("secondary_text")
                }
                for pred in data.get("predictions", [])
            ]
            
        except Exception as e:
            print(f"Google Places autocomplete error: {e}")
            return []
    
    def _parse_results(self, results: List[Dict]) -> List[Dict[str, Any]]:
        """Parse search results into a consistent format."""
        parsed = []
        for place in results[:10]:  # Limit to 10 results
            parsed.append({
                "place_id": place.get("place_id"),
                "name": place.get("name"),
                "address": place.get("formatted_address"),
                "latitude": place.get("geometry", {}).get("location", {}).get("lat"),
                "longitude": place.get("geometry", {}).get("location", {}).get("lng"),
                "rating": place.get("rating"),
                "user_ratings_total": place.get("user_ratings_total"),
                "price_level": place.get("price_level"),
                "types": place.get("types", []),
                "opening_hours": place.get("opening_hours", {}).get("open_now"),
                "photo_reference": place.get("photos", [{}])[0].get("photo_reference") if place.get("photos") else None
            })
        return parsed
    
    def _parse_place_details(self, place: Dict) -> Dict[str, Any]:
        """Parse place details into a consistent format."""
        return {
            "place_id": place.get("place_id"),
            "name": place.get("name"),
            "address": place.get("formatted_address"),
            "phone": place.get("formatted_phone_number"),
            "website": place.get("website"),
            "google_maps_url": place.get("url"),
            "latitude": place.get("geometry", {}).get("location", {}).get("lat"),
            "longitude": place.get("geometry", {}).get("location", {}).get("lng"),
            "rating": place.get("rating"),
            "price_level": place.get("price_level"),
            "types": place.get("types", []),
            "opening_hours": place.get("opening_hours", {}).get("weekday_text", []),
            "reviews": [
                {
                    "author": r.get("author_name"),
                    "rating": r.get("rating"),
                    "text": r.get("text")[:200] if r.get("text") else None
                }
                for r in place.get("reviews", [])[:3]
            ]
        }
    
    def get_photo_url(self, photo_reference: str, max_width: int = 400) -> str:
        """Get photo URL from photo reference."""
        return f"{self.BASE_URL}/photo?maxwidth={max_width}&photo_reference={photo_reference}&key={self.api_key}"
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Singleton instance
_places_tool: Optional[GooglePlacesTool] = None


def get_places_tool() -> GooglePlacesTool:
    """Get or create the Google Places tool instance."""
    global _places_tool
    if _places_tool is None:
        _places_tool = GooglePlacesTool()
    return _places_tool
