"""
Watchout Backend - Food Agent
"""
from typing import Dict, Any, Optional, List
from app.agents.base import BaseAgent
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
        context = context or {}
        city = context.get("city", "")
        
        if not city:
            response_parts = []
            async for chunk in self.stream(f"Food question: {user_input}"):
                response_parts.append(chunk)
            return {"response": "".join(response_parts), "restaurants": None}
        
        # Search restaurants
        results = await self.places.search_places(f"restaurant in {city}", place_type="restaurant")
        restaurants = [
            {
                "name": p.get("name"),
                "rating": p.get("rating"),
                "address": p.get("address"),
                "price_level": p.get("price_level")
            }
            for p in results[:8]
        ]
        
        # Get local specialties
        local_food = await self._get_local_specialties(city)
        
        return {
            "response": self._format_response(city, restaurants, local_food),
            "restaurants": restaurants,
            "local_specialties": local_food
        }
    
    async def _get_local_specialties(self, city: str) -> Dict[str, Any]:
        schema = {
            "type": "object",
            "properties": {
                "must_try_dishes": {"type": "array", "items": {"type": "object", "properties": {"name": {"type": "string"}, "description": {"type": "string"}}}},
                "famous_food_streets": {"type": "array", "items": {"type": "string"}}
            }
        }
        return await self.generate_structured(f"Local food specialties in {city}, India", schema) or {}
    
    def _format_response(self, city: str, restaurants: List, local_food: Dict) -> str:
        response = f"🍽️ **Food Guide: {city}**\n\n"
        
        if local_food.get("must_try_dishes"):
            response += "**Must-Try:**\n"
            for dish in local_food["must_try_dishes"][:4]:
                response += f"• {dish.get('name')} - {dish.get('description', '')}\n"
        
        if restaurants:
            response += "\n**Top Restaurants:**\n"
            for r in sorted(restaurants, key=lambda x: x.get("rating", 0), reverse=True)[:5]:
                response += f"• {r.get('name')} - ⭐{r.get('rating', 'N/A')}\n"
        
        return response
