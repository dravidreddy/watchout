"""
Watchout — MCP Tool Server

Exposes each specialist agent as a standard FastMCP tool.
Agents themselves are unchanged — this is a thin adapter layer.
"""
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from app.agents.clarification import ClarificationAgent
from app.agents.itinerary import ItineraryAgent
from app.agents.weather import WeatherAgent
from app.agents.route import RouteAgent
from app.agents.stay import StayAgent
from app.agents.food import FoodAgent
from app.agents.reviewer import ReviewerAgent
from app.prompts import build_mcp_server_instructions


mcp = FastMCP(
    name="Watchout Travel Tools",
    instructions=build_mcp_server_instructions(),
)

# ---------------------------------------------------------------------------
# Tool: clarify_preferences
# ---------------------------------------------------------------------------

@mcp.tool(
    description=(
        "Extract and clarify travel preferences from user input. "
        "Returns updated preferences dict and missing_fields list. "
        "Call this during the GATHERING phase."
    )
)
async def clarify_preferences(
    user_input: str,
    preferences: Dict[str, Any],
    missing_fields: List[str],
    conversation_history: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    agent = ClarificationAgent()
    return await agent.run(
        user_input,
        context={
            "preferences": preferences,
            "missing_fields": missing_fields,
            "conversation_history": conversation_history or [],
        },
    )


# ---------------------------------------------------------------------------
# Tool: build_itinerary  (per-city aware)
# ---------------------------------------------------------------------------

@mcp.tool(
    description=(
        "Generate a detailed day-by-day itinerary for a single city leg. "
        "Call once per city in parallel for multi-city trips."
    )
)
async def build_itinerary(
    city: str,
    days: int,
    preferences: Dict[str, Any],
    weather_data: Optional[Dict[str, Any]] = None,
    budget_per_day: Optional[float] = None,
    vibe: Optional[List[str]] = None,
) -> Dict[str, Any]:
    agent = ItineraryAgent()
    ctx: Dict[str, Any] = {
        "preferences": {
            **preferences,
            "destinations": [city],
            "duration_days": days,
        },
        "weather_data": weather_data or {},
        "timezone_id": preferences.get("timezone_id", "Asia/Kolkata"),
    }
    if budget_per_day:
        ctx["preferences"]["budget_per_day"] = budget_per_day
    if vibe:
        ctx["preferences"]["travel_vibe"] = vibe

    result = await agent.run("", ctx)
    result["_city"] = city  # tag result for fan-out merge
    return result


# ---------------------------------------------------------------------------
# Tool: get_weather
# ---------------------------------------------------------------------------

@mcp.tool(
    description=(
        "Fetch weather forecast and seasonal advice for a city. "
        "Call in parallel across all cities before itinerary generation."
    )
)
async def get_weather(
    city: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    agent = WeatherAgent()
    result = await agent.run(
        "",
        context={
            "city": city,
            "preferences": {
                "destinations": [city],
                "start_date": start_date,
                "end_date": end_date,
            },
        },
    )
    result["_city"] = city
    return result


# ---------------------------------------------------------------------------
# Tool: compute_intercity_route
# ---------------------------------------------------------------------------

@mcp.tool(
    description=(
        "Calculate travel route and estimated time between two cities. "
        "Call sequentially in city order for multi-city trips."
    )
)
async def compute_intercity_route(
    origin_city: str,
    destination_city: str,
    transport_preference: str = "flexible",
) -> Dict[str, Any]:
    agent = RouteAgent()
    result = await agent.run(
        "",
        context={
            "stops": [
                {"name": origin_city},
                {"name": destination_city},
            ],
            "transport_preference": transport_preference,
        },
    )
    result["_leg"] = f"{origin_city}→{destination_city}"
    return result


# ---------------------------------------------------------------------------
# Tool: compute_day_routes  (within a city)
# ---------------------------------------------------------------------------

@mcp.tool(
    description="Optimise the daily route within a city given a list of activity stops."
)
async def compute_day_routes(
    stops: List[Dict[str, Any]],
    city: str,
) -> Dict[str, Any]:
    agent = RouteAgent()
    result = await agent.run("", context={"stops": stops, "city": city})
    result["_city"] = city
    return result


# ---------------------------------------------------------------------------
# Tool: find_stays
# ---------------------------------------------------------------------------

@mcp.tool(
    description=(
        "Find accommodation options for a city. "
        "Call in parallel across all cities during the PLANNING phase."
    )
)
async def find_stays(
    city: str,
    days: int,
    budget_range: str,
    preferences: Dict[str, Any],
) -> Dict[str, Any]:
    agent = StayAgent()
    result = await agent.run(
        "",
        context={
            "city": city,
            "budget": budget_range.replace("-", "_"),
            "days": days,
            "preferences": preferences,
        },
    )
    result["_city"] = city
    return result


# ---------------------------------------------------------------------------
# Tool: find_food
# ---------------------------------------------------------------------------

@mcp.tool(
    description=(
        "Recommend restaurants and local food experiences for a city. "
        "Call in parallel across all cities during the PLANNING phase."
    )
)
async def find_food(
    city: str,
    preferences: Dict[str, Any],
    vibe: Optional[List[str]] = None,
) -> Dict[str, Any]:
    agent = FoodAgent()
    ctx_prefs = {**preferences}
    if vibe:
        ctx_prefs["travel_vibe"] = vibe
    result = await agent.run("", context={"city": city, "preferences": ctx_prefs})
    result["_city"] = city
    return result


# ---------------------------------------------------------------------------
# Tool: review_itinerary
# ---------------------------------------------------------------------------

@mcp.tool(
    description=(
        "Review a generated itinerary for quality, feasibility and consistency. "
        "Returns the itinerary (possibly revised) and any issues found."
    )
)
async def review_itinerary(
    itinerary: Dict[str, Any],
    preferences: Dict[str, Any],
) -> Dict[str, Any]:
    agent = ReviewerAgent()
    return await agent.run(
        "",
        context={
            "itinerary": itinerary,
            "preferences": preferences,
        },
    )
