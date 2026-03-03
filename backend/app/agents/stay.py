"""
Watchout Backend - Stay Agent
"""
from typing import Dict, Any, Optional, List

from app.agents.base import BaseAgent
from app.prompts import build_stay_general_prompt, build_stay_recommendations_prompt
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
        Returns standardized format: {response, data, error}
        """
        context = context or {}
        city = context.get("city", "")
        budget = context.get("budget", "mid_range")
        preferences = context.get("preferences", {})
        
        if not city:
            result = await self._handle_general_query(user_input)
            return {
                "response": result["response"],
                "data": {"accommodations": None},
                "error": None
            }
        
        # Search for hotels
        try:
            accommodations = await self._search_accommodations(
                city, budget, preferences
            )
            
            return {
                "response": self._format_response(city, accommodations),
                "data": {"accommodations": accommodations},
                "error": None
            }
        except Exception as e:
            return {
                "response": "I couldn't fetch hotel options right now.",
                "data": {},
                "error": str(e)
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
        """Generate personalized recommendations with full traveler context."""
        num_travelers = preferences.get("num_travelers", 1)
        travel_style = preferences.get("travel_style", "not specified")
        vibe = preferences.get("travel_vibe", [])
        vibe_str = ", ".join(vibe) if isinstance(vibe, list) else str(vibe) if vibe else "not specified"
        start_date = preferences.get("start_date", "?")
        end_date = preferences.get("end_date", "?")

        # Budget price ranges for guidance
        budget_guide = {
            "budget": "INR 800-2,500/night",
            "mid_range": "INR 2,500-8,000/night",
            "luxury": "INR 12,000+/night"
        }.get(budget, "mid-range pricing")

        prompt = build_stay_recommendations_prompt(
            city=city,
            options=options,
            num_travelers=num_travelers,
            travel_style=travel_style,
            vibe_str=vibe_str,
            budget=budget,
            budget_guide=budget_guide,
            start_date=start_date,
            end_date=end_date,
        )

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
                            "neighborhood_notes": {"type": "string"},
                            "caution": {"type": "string"},
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
        """Handle general accommodation queries with warmth and India context."""
        response_parts = []

        async for chunk in self.stream(build_stay_general_prompt(query)):
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
        """Format accommodation options as a conversational response."""
        response = f"I've found some great places to stay in **{city}**.\n\n"
        
        # Recommendations
        recommendations = accommodations.get("recommendations", [])
        if recommendations:
            response += "Based on your preferences, here are my top picks:\n\n"
            for rec in recommendations[:3]:
                response += f"- **{rec.get('name', 'Option')}**: {rec.get('reason', '')} (Best for: {rec.get('best_for', 'All travelers')})\n"
                if rec.get("estimated_price"):
                    response += f"  (Approx. {rec['estimated_price']})\n"
            response += "\n"
        
        # All options summary
        options = accommodations.get("options", [])
        if options and not recommendations:
             # Fallback if no specific recommendations
            response += f"I found **{len(options)} options** ranging from hostels to luxury resorts.\n"
            top_rated = sorted(options, key=lambda x: x.get("rating", 0), reverse=True)[:3]
            for opt in top_rated:
                stars = "*" * int(opt.get("rating", 0))
                response += f"- **{opt.get('name')}** {stars} ({opt.get('rating', 'N/A')})\n"
            response += "\n"

        # Booking links
        links = accommodations.get("booking_links", {})
        if links:
            response += "You can check availability and book here:\n"
            response += f"- [Booking.com]({links.get('booking', '')}) | [Airbnb]({links.get('airbnb', '')}) | [MakeMyTrip]({links.get('makemytrip', '')})"
        
        return response

