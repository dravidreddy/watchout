"""
Watchout Backend - Itinerary Parser Service
Extracts structured itinerary data from conversation history.
"""
from typing import Dict, Any, Optional, List
import json
import logging
from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)
from app.services.conversation_manager import conversation_manager


class ItineraryParser(BaseAgent):
    """
    Service for extracting structured travel data from conversations.
    """
    
    def __init__(self):
        super().__init__(
            name="Itinerary Data Extractor",
            description="Extracts structured trip details (cities, dates, daily plans) from chat history.",
            model_type="main"
        )
        
    async def parse_conversation(self, history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Extract structured trip data from the provided conversation history.
        """
        if not history:
            return None
            
        history_str = conversation_manager.format_history_for_llm(history, max_messages=20)
        
        prompt = f"""Extract the current planned itinerary from the following conversation history.
If certain details are missing or not yet decided, omit them or leave them as null/empty.

CONVERSATION HISTORY:
{history_str}

EXTRACTOR GOAL:
Identify the current state of the trip plan including:
1. Trip title (come up with a catchy generic one if not specified)
2. List of cities mentioned as destinations
3. Start and end dates (if mentioned, format as YYYY-MM-DD)
4. Number of travelers
5. Total budget in INR (if mentioned)
6. A day-by-day breakdown of activities mentioned so far.

If the user just started and hasn't fixed anything, return the best guess based on the chat.
"""

        schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "cities": {"type": "array", "items": {"type": "string"}},
                "start_date": {"type": "string", "description": "ISO format date YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "ISO format date YYYY-MM-DD"},
                "num_days": {"type": "integer"},
                "num_travelers": {"type": "integer"},
                "budget_total": {"type": "integer"},
                "days": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "day_number": {"type": "integer"},
                            "city": {"type": "string"},
                            "activities": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "time": {"type": "string"},
                                        "name": {"type": "string"},
                                        "description": {"type": "string"},
                                        "duration_minutes": {"type": "integer"},
                                        "estimated_cost": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "required": ["cities"]
        }
        
        try:
            result = await self.generate_structured(prompt, schema)
            return result
        except Exception as e:
            logger.warning("Error in ItineraryParser: %s", e)
            return None

    async def run(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Implementation of the abstract method from BaseAgent.
        This parser is typically called via parse_conversation, but run is required by the base class.
        """
        return {"error": "Use parse_conversation for structured extraction"}


# Singleton
itinerary_parser = ItineraryParser()
