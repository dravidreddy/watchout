"""
Watchout Backend - Stay Agent
"""
from typing import Dict, Any, Optional, List

from app.agents.base import BaseAgent
from app.tools.google_places import get_places_tool


class StayAgent(BaseAgent):
    """
    Agent that suggests accommodation options.
    Uses Google Places for real data and provides booking links.
    """
    
    def __init__(self):
        super().__init__(
            name="Stay Finder",
            description="""You help find perfect accommodations in India.
You consider:
- Budget (hostels, budget hotels, mid-range, luxury)
- Style (heritage, boutique, resort, modern)
- Location (near attractions, safe areas, good transport)
- Amenities (WiFi, breakfast, pool, parking)
- Reviews and ratings

Provide real options with booking links."""
        )
        self.places = get_places_tool()
        
        self.booking_urls = {
            "booking": "https://www.booking.com",
            "makemytrip": "https://www.makemytrip.com/hotels",
            "goibibo": "https://www.goibibo.com/hotels/",
            "airbnb": "https://www.airbnb.co.in",
            "oyo": "https://www.oyorooms.com"
        }
    
    async def run(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Find accommodation options for a destination.
        
        Context should include:
        - city: Destination city
        - budget: Budget level
        - preferences: Accommodation preferences
        - check_in: Check-in date
        - check_out: Check-out date
        """
        context = context or {}
        city = context.get("city", "")
        budget = context.get("budget", "mid_range")
        preferences = context.get("preferences", {})
        
        if not city:
            return await self._handle_general_query(user_input)
        
        # Search for hotels
        accommodations = await self._search_accommodations(
            city, budget, preferences
        )
        
        return {
            "response": self._format_response(city, accommodations),
            "accommodations": accommodations
        }
    
    async def _search_accommodations(
        self,
        city: str,
        budget: str,
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Search for accommodations using Google Places."""
        
        # Determine hotel type based on budget
        hotel_types = {
            "budget": ["hostel", "budget hotel", "guesthouse"],
            "mid_range": ["hotel", "resort"],
            "luxury": ["luxury hotel", "5 star hotel", "resort"]
        }
        
        search_terms = hotel_types.get(budget, ["hotel"])
        
        all_options = []
        
        for term in search_terms:
            query = f"{term} in {city}"
            results = await self.places.search_places(query, place_type="lodging")
            
            for place in results[:5]:
                option = {
                    "name": place.get("name"),
                    "place_id": place.get("place_id"),
                    "address": place.get("address"),
                    "rating": place.get("rating"),
                    "reviews_count": place.get("user_ratings_total"),
                    "price_level": place.get("price_level"),
                    "latitude": place.get("latitude"),
                    "longitude": place.get("longitude"),
                    "type": term
                }
                
                # Get photo if available
                if place.get("photo_reference"):
                    option["photo_url"] = self.places.get_photo_url(
                        place["photo_reference"]
                    )
                
                all_options.append(option)
        
        # Get recommendations
        recommendations = await self._generate_recommendations(
            city, budget, all_options[:10], preferences
        )
        
        return {
            "options": all_options[:10],
            "recommendations": recommendations,
            "booking_links": self._get_booking_links(city)
        }
    
    async def _generate_recommendations(
        self,
        city: str,
        budget: str,
        options: List[Dict],
        preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate personalized recommendations."""
        
        prompt = f"""Based on these accommodation options in {city}:
{options[:5]}

Budget level: {budget}
Preferences: {preferences}

Recommend the top 3 options with reasons why they'd be great for this traveler."""
        
        schema = {
            "type": "object",
            "properties": {
                "recommendations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "reason": {"type": "string"},
                            "best_for": {"type": "string"},
                            "estimated_price": {"type": "string"}
                        }
                    }
                }
            }
        }
        
        result = await self.generate_structured(prompt, schema)
        return result.get("recommendations", []) if result else []
    
    async def _handle_general_query(self, query: str) -> Dict[str, Any]:
        """Handle general accommodation queries."""
        response_parts = []
        
        async for chunk in self.stream(
            f"Answer this accommodation question for India travel: {query}"
        ):
            response_parts.append(chunk)
        
        return {
            "response": "".join(response_parts),
            "accommodations": None
        }
    
    def _get_booking_links(self, city: str) -> Dict[str, str]:
        """Get booking links for different platforms."""
        city_slug = city.lower().replace(" ", "-")
        return {
            "booking": f"{self.booking_urls['booking']}/searchresults.html?ss={city}",
            "makemytrip": f"{self.booking_urls['makemytrip']}/{city_slug}-hotels",
            "goibibo": f"{self.booking_urls['goibibo']}{city_slug}-hotels",
            "airbnb": f"{self.booking_urls['airbnb']}/s/{city}/homes",
            "oyo": f"{self.booking_urls['oyo']}/search?location={city}"
        }
    
    def _format_response(
        self,
        city: str,
        accommodations: Dict[str, Any]
    ) -> str:
        """Format accommodation options as a response."""
        response = f"""🏨 **Accommodations in {city}**

"""
        
        # Recommendations
        recommendations = accommodations.get("recommendations", [])
        if recommendations:
            response += "**Top Recommendations:**\n"
            for i, rec in enumerate(recommendations[:3], 1):
                response += f"\n{i}. **{rec.get('name', 'Option')}**\n"
                response += f"   {rec.get('reason', '')}\n"
                response += f"   Best for: {rec.get('best_for', 'All travelers')}\n"
                if rec.get("estimated_price"):
                    response += f"   Price: {rec['estimated_price']}\n"
        
        # All options summary
        options = accommodations.get("options", [])
        if options:
            response += f"\n**Found {len(options)} options** ranging from hostels to hotels.\n"
            
            # Show top rated
            top_rated = sorted(options, key=lambda x: x.get("rating", 0), reverse=True)[:3]
            response += "\n**Highest Rated:**\n"
            for opt in top_rated:
                stars = "⭐" * int(opt.get("rating", 0))
                response += f"• {opt.get('name')} - {opt.get('rating', 'N/A')} {stars}\n"
        
        # Booking links
        links = accommodations.get("booking_links", {})
        response += "\n🔗 **Book Here:**\n"
        response += f"• [Booking.com]({links.get('booking', '')})\n"
        response += f"• [MakeMyTrip]({links.get('makemytrip', '')})\n"
        response += f"• [Airbnb]({links.get('airbnb', '')})\n"
        response += f"• [OYO]({links.get('oyo', '')})\n"
        
        return response
