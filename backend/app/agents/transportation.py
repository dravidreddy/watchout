"""
Watchout Backend - Transportation Agent
"""
from typing import Dict, Any, Optional, List

from app.agents.base import BaseAgent
from app.prompts import build_transport_general_prompt, build_transport_recommendations_prompt
from app.tools.tavily_search import get_tavily_tool


class TransportationAgent(BaseAgent):
    """
    Agent that suggests transportation options between cities.
    Provides redirect links for booking flights, trains, and buses.
    """
    
    def __init__(self):
        super().__init__(
            name="Transport Specialist",
            description="""You help find the best transportation options in India.
You know about:
- Flights (IndiGo, SpiceJet, Air India, Vistara)
- Trains (Indian Railways/IRCTC - Rajdhani, Shatabdi, Duronto)
- Buses (RedBus, KSRTC, MSRTC, private Volvo)
- Cabs (Ola, Uber)

Since direct booking APIs are limited, you provide:
- Recommendations based on route and budget
- Redirect links to official booking sites
- Tips for booking (Tatkal, advance booking windows)
- Approximate prices and travel times"""
        )
        self.tavily = get_tavily_tool()
        
        # Booking URLs for redirect
        self.booking_urls = {
            "irctc": "https://www.irctc.co.in/nget/train-search",
            "redbus": "https://www.redbus.in",
            "makemytrip_flights": "https://www.makemytrip.com/flights/",
            "makemytrip_trains": "https://www.makemytrip.com/railways/",
            "makemytrip_buses": "https://www.makemytrip.com/bus-tickets/",
            "ixigo_flights": "https://www.ixigo.com/flights",
            "ixigo_trains": "https://www.ixigo.com/trains",
            "ola": "https://www.olacabs.com",
            "uber": "https://www.uber.com/in/en/"
        }
    
    async def run(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Find transportation options between cities.
        Returns standardized format: {response, data, error}
        """
        context = context or {}
        from_city = context.get("from_city", "")
        to_city = context.get("to_city", "")
        travel_date = context.get("date", "")
        budget = context.get("budget", "mid_range")
        
        if not from_city or not to_city:
            # Try to extract from user input
            result = await self._handle_general_query(user_input)
            return {
                "response": result["response"],
                "data": {"options": None},
                "error": None
            }
        
        # Get options for all transport modes
        try:
            options = await self._get_transport_options(
                from_city, to_city, travel_date, budget
            )
            
            return {
                "response": self._format_response(from_city, to_city, options),
                "data": {"options": options},
                "error": None
            }
        except Exception as e:
            return {
                "response": "Unavailable to fetch transport options at the moment.",
                "data": {},
                "error": str(e)
            }
    
    async def _get_transport_options(
        self,
        from_city: str,
        to_city: str,
        travel_date: str,
        budget: str
    ) -> Dict[str, Any]:
        """Get transportation options for a route."""
        options = {
            "flights": [],
            "trains": [],
            "buses": [],
            "cabs": None
        }
        
        # Search for real-time info
        search_query = f"travel from {from_city} to {to_city} India flights trains buses price time"
        search_results = await self.tavily.search(search_query)
        
        # Generate recommendations based on route and research
        recommendations = await self._generate_recommendations(
            from_city, to_city, budget, search_results
        )
        
        if recommendations:
            options = recommendations
        
        # Add booking links
        options["booking_links"] = self._get_booking_links(from_city, to_city)
        
        return options
    
    async def _generate_recommendations(
        self,
        from_city: str,
        to_city: str,
        budget: str,
        search_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate transport recommendations using LLM with India-specific expertise."""
        search_context = ""
        if search_data:
            search_context = f"\nRecent search data: {search_data.get('answer', '')}"

        # Budget-based class recommendation
        class_guide = {
            "budget": "Sleeper (SL) or 3AC for overnight; State bus for short routes",
            "mid_range": "3AC or 2AC for trains; Volvo AC bus overnight",
            "luxury": "1AC Rajdhani/Shatabdi; Vistara/Air India direct; private cab"
        }.get(budget, "3AC for trains")

        prompt = build_transport_recommendations_prompt(
            from_city=from_city,
            to_city=to_city,
            budget=budget,
            class_guide=class_guide,
            search_context=search_context,
        )

        schema = {
            "type": "object",
            "properties": {
                "recommended_mode": {"type": "string"},
                "flights": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "airlines": {"type": "array", "items": {"type": "string"}},
                            "duration": {"type": "string"},
                            "price_range": {"type": "string"},
                            "frequency": {"type": "string"}
                        }
                    }
                },
                "trains": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "number": {"type": "string"},
                            "duration": {"type": "string"},
                            "classes": {"type": "array", "items": {"type": "string"}},
                            "price_range": {"type": "string"},
                            "booking_tip": {"type": "string"}
                        }
                    }
                },
                "buses": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "operators": {"type": "array", "items": {"type": "string"}},
                            "duration": {"type": "string"},
                            "price_range": {"type": "string"}
                        }
                    }
                },
                "cab_info": {
                    "type": "object",
                    "properties": {
                        "available": {"type": "boolean"},
                        "estimated_cost": {"type": "string"},
                        "duration": {"type": "string"}
                    }
                },
                "golden_tip": {"type": "string"},
                "tips": {"type": "array", "items": {"type": "string"}}
            }
        }

        result = await self.generate_structured(prompt, schema)
        return result or {}
    
    async def _handle_general_query(self, query: str) -> Dict[str, Any]:
        """Handle general transportation queries with India expertise."""
        response_parts = []

        async for chunk in self.stream(build_transport_general_prompt(query)):
            response_parts.append(chunk)

        return {
            "response": "".join(response_parts),
            "options": None
        }
    
    def _get_booking_links(
        self,
        from_city: str,
        to_city: str
    ) -> Dict[str, str]:
        """Get booking links for different platforms."""
        return {
            "irctc": f"{self.booking_urls['irctc']}",
            "redbus": f"{self.booking_urls['redbus']}/bus-tickets/{from_city.lower()}-to-{to_city.lower()}",
            "makemytrip_flights": f"{self.booking_urls['makemytrip_flights']}",
            "makemytrip_trains": f"{self.booking_urls['makemytrip_trains']}",
            "ixigo": f"{self.booking_urls['ixigo_trains']}"
        }
    
    def _format_response(
        self,
        from_city: str,
        to_city: str,
        options: Dict[str, Any]
    ) -> str:
        """Format transport options as a conversational response."""
        response = f"Here are the best ways to get from **{from_city}** to **{to_city}**.\n\n"
        
        recommended = options.get("recommended_mode", "train")
        response += f"I recommend taking a **{recommended}** for this route.\n\n"
        
        # Flights
        flights = options.get("flights", [])
        if flights:
            response += "**Flights:**\n"
            for flight in flights[:2]:
                airlines = ", ".join(flight.get("airlines", ["Multiple airlines"]))
                response += f"- {airlines} take about {flight.get('duration', 'N/A')}"
                if flight.get('price_range'):
                    response += f" ({flight.get('price_range')})"
                response += ".\n"
            response += "\n"
        
        # Trains
        trains = options.get("trains", [])
        if trains:
            response += "**Trains:**\n"
            for train in trains[:3]:
                response += f"- {train.get('name', 'Train')}: {train.get('duration', 'N/A')}"
                if train.get('price_range'):
                     response += f" approx {train.get('price_range')}"
                response += "\n"
            response += "\n"
        
        # Buses
        buses = options.get("buses", [])
        if buses:
            response += "**Buses:**\n"
            for bus in buses[:2]:
                response += f"- {bus.get('type', 'Bus')}: {bus.get('duration', 'N/A')}\n"
            response += "\n"
        
        # Tips including in natural flow
        tips = options.get("tips", [])
        if tips:
            response += "**Pro Tip:** " + " ".join(tips[:2]) + "\n\n"
        
        # Booking links compact
        links = options.get("booking_links", {})
        if links:
            links_list = []
            if links.get("irctc"): links_list.append(f"[IRCTC]({links['irctc']})")
            if links.get("redbus"): links_list.append(f"[RedBus]({links['redbus']})")
            if links.get("makemytrip_flights"): links_list.append(f"[Flights]({links['makemytrip_flights']})")
            
            if links_list:
                response += f"Book here: {' | '.join(links_list)}"
        
        return response

