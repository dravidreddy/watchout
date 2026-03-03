"""
Watchout Backend - Food Agent
"""
from typing import Dict, Any, Optional, List
from app.agents.base import BaseAgent
from app.prompts import build_food_general_prompt, build_food_specialties_prompt
from app.tools.google_places import get_places_tool


class FoodAgent(BaseAgent):
    """Agent that recommends restaurants and food experiences."""
    
    def __init__(self):
        super().__init__(
            name="Food Guide",
            description="You recommend local food, restaurants, and dining experiences in India."
        )
        self.places = get_places_tool()
    
    async def run(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Find food options for a city.
        Returns standardized format: {response, data, error}
        """
        context = context or {}
        city = context.get("city", "")
        preferences = context.get("preferences", {})

        if not city:
            # Try to get city from preferences
            destinations = preferences.get("destinations", [])
            city = destinations[0] if destinations else ""

        if not city:
            response_parts = []
            async for chunk in self.stream(build_food_general_prompt(user_input)):
                response_parts.append(chunk)

            return {
                "response": "".join(response_parts),
                "data": {"restaurants": None},
                "error": None
            }
        
        try:
            # Search restaurants
            results = await self.places.search_places(f"best local restaurants in {city}", place_type="restaurant")
            restaurants = [
                {
                    "name": p.get("name"),
                    "rating": p.get("rating"),
                    "address": p.get("address"),
                    "price_level": p.get("price_level")
                }
                for p in results[:8]
            ]

            # Get local specialties with traveler preferences
            local_food = await self._get_local_specialties(city, preferences)
            
            return {
                "response": self._format_response(city, restaurants, local_food),
                "data": {
                    "restaurants": restaurants,
                    "local_specialties": local_food
                },
                "error": None
            }
        except Exception as e:
            return {
                "response": "I couldn't fetch food recommendations right now.",
                "data": {},
                "error": str(e)
            }
    
    async def _get_local_specialties(self, city: str, preferences: Optional[Dict] = None) -> Dict[str, Any]:
        preferences = preferences or {}
        dietary = preferences.get("food_preferences", [])
        dietary_str = ", ".join(dietary) if dietary else "no restrictions"
        budget = preferences.get("budget_range", "mid_range")
        vibe = preferences.get("travel_vibe", [])
        vibe_str = ", ".join(vibe) if isinstance(vibe, list) else str(vibe) if vibe else "general"

        schema = {
            "type": "object",
            "properties": {
                "must_try_dishes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "where_to_find": {"type": "string"}
                        }
                    }
                },
                "famous_food_streets": {"type": "array", "items": {"type": "string"}},
                "dining_tips": {"type": "string"}
            }
        }

        prompt = build_food_specialties_prompt(
            city=city,
            dietary_str=dietary_str,
            budget=budget,
            vibe_str=vibe_str,
        )

        return await self.generate_structured(prompt, schema) or {}
    
    def _format_response(self, city: str, restaurants: List, local_food: Dict) -> str:
        """Format food recommendations as a conversational response."""
        response = f"Get ready to eat your way through **{city}**!\n\n"
        
        # Local specialties
        must_try = local_food.get("must_try_dishes", [])
        if must_try:
            response += "You absolutely *cannot* leave without trying:\n"
            for dish in must_try[:3]:
                response += f"- **{dish.get('name')}**: {dish.get('description', '')}\n"
            response += "\n"
        
        # Restaurants
        if restaurants:
            response += "**Top spots to grab a bite:**\n"
            # Sort by rating
            sorted_restaurants = sorted(restaurants, key=lambda x: x.get("rating", 0), reverse=True)
            for r in sorted_restaurants[:4]:
                price = r.get("price_level") or ""
                rating = r.get("rating", "N/A")
                response += f"- **{r.get('name')}** {price} (rating {rating}): {r.get('address', 'City center')}\n"
        
        return response

