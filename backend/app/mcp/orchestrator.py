"""
Watchout — Stateful MCP Orchestrator

Replaces SupervisorAgent. Uses the MCP tool server via in-process transport.
The state machine (TripStateMachine) drives ALL phase transitions — the LLM
only decides which tools to call within a phase.

SSE event protocol (unchanged from existing frontend contract):
  {type: "status",  agent, status}
  {type: "token",   content}
  {type: "data",    data_type, data}
  {type: "done",    trip_id, is_complete}
  {type: "error",   error}
  {type: "cancelled"}
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, AsyncGenerator, Dict, List, Optional

try:
    # fastmcp export path can vary between versions
    from fastmcp import Client
except Exception:  # pragma: no cover - import-compat fallback
    from fastmcp.client import Client
from fastmcp.client.transports import FastMCPTransport

from app.mcp.server import mcp
from app.mcp.state import CitySegment, TripState, TripStateMachine

logger = logging.getLogger(__name__)

# One shared in-process transport — zero serialization overhead
_transport = FastMCPTransport(mcp)


def _safe(results: list, idx: int, fallback: Any = None) -> Any:
    """Return result at index, or fallback if it raised an exception."""
    v = results[idx] if idx < len(results) else fallback
    if isinstance(v, Exception):
        logger.warning("Tool call %d failed: %s", idx, v)
        return fallback
    return v


def _json_safe(obj: Any) -> Any:
    """Recursively convert a value into a JSON-serializable primitive.

    MongoDB documents contain ObjectId and datetime values that cannot be
    serialized by FastMCP's internal JSON validation.  This function strips
    them to str/int/float/bool/None/list/dict so call_tool() never raises a
    TypeError during argument serialization.
    """
    import datetime
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    # datetime → ISO string
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    # bson.ObjectId, UUID, or anything else → str
    return str(obj)




class WatchoutOrchestrator:
    """
    Stateful orchestrator that drives the travel planning conversation.

    Call `process()` to get an async generator of SSE-compatible event dicts.
    """

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def process(
        self,
        user_id: str,
        message: str,
        trip_context: Dict[str, Any],
        conversation_history: List[Dict[str, Any]],
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Yield SSE events for a single user message.
        Manages phase transitions, parallel tool execution, and context persistence.
        """
        preferences = dict(trip_context.get("preferences") or {})
        raw_state = trip_context.get("trip_state", TripState.GATHERING)
        try:
            state = TripState(raw_state)
        except ValueError:
            state = TripState.GATHERING

        sm = TripStateMachine(preferences, state)

        # Greeting → Gathering on first message
        if sm.state == TripState.GREETING:
            sm.state = TripState.GATHERING

        async with Client(_transport) as client:
            # ── Phase: GATHERING ────────────────────────────────────────
            if sm.state == TripState.GATHERING:
                async for event in self._gathering_phase(
                    client, sm, message, conversation_history
                ):
                    yield event

            # ── Phase: CONFIRMING ───────────────────────────────────────
            elif sm.state == TripState.CONFIRMING:
                # User has just confirmed — advance to planning
                sm.state = TripState.PLANNING
                async for event in self._planning_phase(client, sm):
                    yield event

            # ── Phase: PLANNING (direct trigger, e.g. re-planning) ──────
            elif sm.state == TripState.PLANNING:
                async for event in self._planning_phase(client, sm):
                    yield event

            else:
                # Already complete — allow freeform follow-up questions
                async for event in self._gathering_phase(
                    client, sm, message, conversation_history
                ):
                    yield event

        # Final done event
        yield {
            "type": "done",
            "is_complete": sm.is_complete,
            "trip_state": sm.state.value,
            "preferences": sm.preferences,
        }

    # ------------------------------------------------------------------
    # GATHERING phase — clarification loop
    # ------------------------------------------------------------------

    async def _gathering_phase(
        self,
        client: Client,
        sm: TripStateMachine,
        message: str,
        history: List[Dict[str, Any]],
    ) -> AsyncGenerator[Dict[str, Any], None]:
        yield {"type": "status", "agent": "Travel Buddy", "status": "Understanding your trip..."}

        # Sanitise conversation_history — MongoDB docs contain non-JSON-serializable
        # fields (ObjectId, datetime). FastMCP validates tool arguments through its
        # JSON schema pipeline, so any non-serializable value causes a TypeError → ToolError.
        safe_history = [
            {
                "role": str(m.get("role", "user")),
                "content": str(m.get("content", ""))[:400],  # trim to save tokens
            }
            for m in history[-20:]
        ]

        try:
            result = await client.call_tool(
                "clarify_preferences",
                {
                    "user_input": message,
                    "preferences": _json_safe(sm.preferences),
                    "missing_fields": sm.missing_fields,
                    "conversation_history": safe_history,
                },
            )
        except Exception as e:
            logger.error("clarify_preferences failed: %s", e, exc_info=True)
            yield {"type": "error", "error": "Could not process your message. Please try again."}
            return

        # Unpack result — fastmcp wraps tool returns in a CallToolResult with .data as a list
        # of TextContent items. Guard against all shapes: list, dict, or raw string.
        tool_data = _extract_tool_data(result)

        new_prefs = tool_data.get("preferences") or {}
        assistant_message = tool_data.get("assistant_message") or tool_data.get("response", "")

        # Merge and update state machine
        sm = sm.merge_preferences(new_prefs)

        # Emit the assistant's conversational response as tokens
        if assistant_message:
            yield {"type": "token", "content": assistant_message}

        # Emit updated preferences for DB persistence
        yield {
            "type": "data",
            "data_type": "preferences",
            "data": sm.preferences,
        }

        # Check if gathering is complete
        if sm.is_complete:
            sm.state = TripState.CONFIRMING
            # ── CRITICAL: persist the CONFIRMING state so next turn triggers planning ──
            # Without this, MongoDB still has trip_state="gathering" and the next message
            # (user clicking Confirm) goes back to ClarificationAgent instead of planning.
            yield {
                "type": "data",
                "data_type": "trip_state",
                "data": {"state": sm.state.value, "missing_fields": []},
            }
            # Emit confirmation card data
            yield {
                "type": "data",
                "data_type": "confirmation_required",
                "data": {
                    **sm.preferences,
                    "city_segments": [
                        seg.to_dict() for seg in sm.build_segments()
                    ],
                },
            }
        else:
            # Still gathering — persist the current state
            yield {
                "type": "data",
                "data_type": "trip_state",
                "data": {"state": sm.state.value, "missing_fields": sm.missing_fields},
            }

    # ------------------------------------------------------------------
    # PLANNING phase — parallel fan-out
    # ------------------------------------------------------------------

    async def _planning_phase(
        self,
        client: Client,
        sm: TripStateMachine,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        segments = sm.build_segments()
        multi_city = len(segments) > 1

        yield {
            "type": "status",
            "agent": "Itinerary Architect",
            "status": f"Planning your {len(segments)}-city trip..." if multi_city else "Building your itinerary...",
        }

        # ── Step 1: Weather for all cities in parallel ─────────────────
        yield {"type": "status", "agent": "Weather Advisor", "status": "Checking weather..."}

        weather_results = await asyncio.gather(
            *[
                client.call_tool("get_weather", {
                    "city": seg.city,
                    "start_date": sm.preferences.get("start_date"),
                    "end_date": sm.preferences.get("end_date"),
                })
                for seg in segments
            ],
            return_exceptions=True,
        )

        weather_by_city: Dict[str, Any] = {}
        for i, seg in enumerate(segments):
            raw = _safe(weather_results, i)
            if raw:
                data = _extract_tool_data(raw)
                weather_by_city[seg.city] = data.get("data", {})

        if weather_by_city:
            yield {"type": "data", "data_type": "weather", "data": weather_by_city}

        # ── Step 2: Itinerary per city in parallel ─────────────────────
        yield {"type": "status", "agent": "Itinerary Architect", "status": "Crafting day plans..."}

        itinerary_results = await asyncio.gather(
            *[
                client.call_tool("build_itinerary", {
                    "city": seg.city,
                    "days": seg.days,
                    "preferences": sm.preferences,
                    "weather_data": weather_by_city.get(seg.city),
                    "budget_per_day": seg.budget_per_day,
                    "vibe": seg.vibe,
                })
                for seg in segments
            ],
            return_exceptions=True,
        )

        city_itineraries: List[Dict[str, Any]] = []
        for i, seg in enumerate(segments):
            raw = _safe(itinerary_results, i)
            if raw:
                data = _extract_tool_data(raw)
                city_itineraries.append({
                    "city": seg.city,
                    "days": seg.days,
                    **data.get("data", data),
                })
            else:
                city_itineraries.append({"city": seg.city, "days": seg.days, "error": "generation_failed"})

        # ── Step 3: Inter-city routes (sequential — order matters) ─────
        intercity_routes: List[Dict[str, Any]] = []
        if multi_city:
            yield {"type": "status", "agent": "Route Navigator", "status": "Planning connections between cities..."}

            intercity_routes: List[Dict[str, Any]] = []
            for i in range(len(segments) - 1):
                try:
                    raw = await client.call_tool("compute_intercity_route", {
                        "origin_city": segments[i].city,
                        "destination_city": segments[i + 1].city,
                        "transport_preference": segments[i + 1].transport_preference,
                    })
                    data = _extract_tool_data(raw)
                    intercity_routes.append({
                        "from": segments[i].city,
                        "to": segments[i + 1].city,
                        **data.get("data", {}),
                    })
                except Exception as e:
                    logger.warning("Intercity route %s→%s failed: %s",
                                   segments[i].city, segments[i + 1].city, e)
                    intercity_routes.append({
                        "from": segments[i].city,
                        "to": segments[i + 1].city,
                        "error": str(e),
                    })

        # ── Step 4: Stays + Food per city in parallel ──────────────────
        yield {"type": "status", "agent": "Stay Finder", "status": "Finding accommodation and dining..."}

        stay_food_tasks = []
        for seg in segments:
            stay_food_tasks.append(client.call_tool("find_stays", {
                "city": seg.city,
                "days": seg.days,
                "budget_range": sm.preferences.get("budget_range", "mid-range"),
                "preferences": sm.preferences,
            }))
            stay_food_tasks.append(client.call_tool("find_food", {
                "city": seg.city,
                "preferences": sm.preferences,
                "vibe": seg.vibe,
            }))

        stay_food_results = await asyncio.gather(*stay_food_tasks, return_exceptions=True)

        stays_by_city: Dict[str, Any] = {}
        food_by_city: Dict[str, Any] = {}
        for i, seg in enumerate(segments):
            stay_raw = _safe(stay_food_results, i * 2)
            food_raw = _safe(stay_food_results, i * 2 + 1)
            if stay_raw:
                stays_by_city[seg.city] = _extract_tool_data(stay_raw).get("data", {})
            if food_raw:
                food_by_city[seg.city] = _extract_tool_data(food_raw).get("data", {})

        # ── Step 5: Assemble full multi-city itinerary ─────────────────
        full_itinerary = _assemble_itinerary(
            segments=segments,
            city_itineraries=city_itineraries,
            intercity_routes=intercity_routes if multi_city else [],
            stays_by_city=stays_by_city,
            food_by_city=food_by_city,
            preferences=sm.preferences,
        )

        # ── Step 6: Review ─────────────────────────────────────────────
        yield {"type": "status", "agent": "Reviewer", "status": "Reviewing and polishing your plan..."}
        try:
            review_raw = await client.call_tool("review_itinerary", {
                "itinerary": full_itinerary,
                "preferences": sm.preferences,
            })
            review_data = _extract_tool_data(review_raw)
            if review_data.get("data", {}).get("revised_itinerary"):
                full_itinerary = review_data["data"]["revised_itinerary"]
        except Exception as e:
            logger.warning("Reviewer failed (using unreviewed itinerary): %s", e)

        # ── Emit final itinerary ────────────────────────────────────────
        sm.state = TripState.COMPLETE
        yield {
            "type": "data",
            "data_type": "itinerary",
            "data": full_itinerary,
        }
        # Emit a summary token
        yield {
            "type": "token",
            "content": _summary_message(segments, full_itinerary),
        }

    # ------------------------------------------------------------------
    # Cancel support (compatibility with existing /cancel endpoint)
    # ------------------------------------------------------------------

    async def cancel_user_task(self, user_id: str) -> bool:
        # Cancellation is handled by the caller dropping the SSE connection.
        # asyncio.CancelledError propagates naturally. Nothing to do here.
        return True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_tool_data(raw: Any) -> Dict[str, Any]:
    """Normalise fastmcp tool result to a plain dict — handles all response shapes."""
    # Already a plain dict (direct return from tool in some fastmcp versions)
    if isinstance(raw, dict):
        return raw

    # Standard fastmcp CallToolResult: .data is a list of TextContent items
    if hasattr(raw, "data") and raw.data:
        data_list = raw.data
        # Defensive: data might be a dict in edge cases — don't subscript with [0]
        if not isinstance(data_list, list):
            if isinstance(data_list, dict):
                return data_list
            try:
                return json.loads(str(data_list))
            except Exception:
                return {}

        if not data_list:  # empty list
            return {}

        item = data_list[0]
        # TextContent has .text attribute
        text = getattr(item, "text", None)
        if text is None:
            text = str(item)
        try:
            return json.loads(text)
        except Exception:
            return {"response": text}

    # Fallback: try to coerce to str and parse
    try:
        return json.loads(str(raw))
    except Exception:
        return {}


def _assemble_itinerary(
    segments: List[CitySegment],
    city_itineraries: List[Dict],
    intercity_routes: List[Dict],
    stays_by_city: Dict[str, Any],
    food_by_city: Dict[str, Any],
    preferences: Dict[str, Any],
) -> Dict[str, Any]:
    """Merge per-city results into one cohesive itinerary object.

    ItineraryModal reads `itinerary.days` (top-level), so we must flatten
    all per-city day plans into a single sequential list.
    """
    cities = [seg.city for seg in segments]
    total_days = sum(seg.days for seg in segments)

    # Flatten all city day plans → single sequential days list
    all_days: List[Dict[str, Any]] = []
    day_counter = 1
    for itin in city_itineraries:
        city_name = itin.get("city", "")
        
        raw_plan = itin.get("raw_plan", {})
        itin_obj = itin.get("itinerary", {})
        
        raw_days = []
        if isinstance(itin_obj, dict) and "days" in itin_obj:
            raw_days = itin_obj["days"]
        elif hasattr(itin_obj, "days"):
            # Handle un-serialized Pydantic objects just in case
            if isinstance(itin_obj.days, list):
                raw_days = [d.dict() if hasattr(d, "dict") else d for d in itin_obj.days]
        
        if not raw_days and isinstance(raw_plan, dict) and "days" in raw_plan:
            raw_days = raw_plan.get("days", [])
            
        if not isinstance(raw_days, list):
            raw_days = []
            
        for day in raw_days:
            if hasattr(day, "dict"):
                day = day.dict()
            if not isinstance(day, dict):
                continue
            all_days.append({
                **day,
                "day_number": day_counter,
                "city": city_name,
                # Attach stay + food for this city so the modal can show them
                "stay": stays_by_city.get(city_name, {}).get("recommendation"),
                "food_spots": food_by_city.get(city_name, {}).get("spots", []),
            })
            day_counter += 1

    # Budget total: prefer explicit, fall back to a simple estimate
    budget_range = preferences.get("budget_range", "mid-range")
    budget_total: Optional[int] = None
    if budget_range == "budget":
        budget_total = total_days * 2000
    elif budget_range == "luxury":
        budget_total = total_days * 12000
    else:
        budget_total = total_days * 5000

    return {
        "title": f"{' → '.join(cities)} Trip",  # overwritten by AI title generator
        "cities": cities,
        "num_days": total_days,
        "num_travelers": preferences.get("num_travelers", 1),
        "start_date": preferences.get("start_date"),
        "end_date": preferences.get("end_date"),
        "budget_range": budget_range,
        "budget_total": budget_total,
        "days": all_days,           # ← ItineraryModal reads this
        "city_segments": [         # ← kept for future reference
            {
                **itin,
                "stays": stays_by_city.get(itin.get("city", ""), {}),
                "food": food_by_city.get(itin.get("city", ""), {}),
            }
            for itin in city_itineraries
        ],
        "intercity_routes": intercity_routes,
        "summary": f"A {total_days}-day adventure across {', '.join(cities)}.",
    }



def _extract_hour(time_text: str) -> Optional[int]:
    match = re.search(r"(\d{1,2})", time_text or "")
    if not match:
        return None
    hour = int(match.group(1))
    if 0 <= hour <= 23:
        return hour
    return None


def _day_part(time_text: str) -> str:
    hour = _extract_hour(time_text)
    if hour is None:
        return "afternoon"
    if hour < 12:
        return "morning"
    if hour < 17:
        return "afternoon"
    return "evening"


def _stop_line(stop: Dict[str, Any]) -> str:
    name = str(stop.get("name") or "Local highlight").strip()
    details: List[str] = []
    when = str(stop.get("time") or stop.get("arrival_time") or "").strip()
    if when:
        details.append(when)
    tip = str(stop.get("description") or stop.get("tips") or "").strip()
    if tip:
        details.append(tip)
    if details:
        return f"{name} ({'; '.join(details)})"
    return name


def _format_stay_hint(raw_stay: Any) -> str:
    if isinstance(raw_stay, str):
        text = raw_stay.strip()
        return text if text else "Flexible by preference"
    if isinstance(raw_stay, dict):
        for key in ("name", "hotel", "neighborhood", "area", "recommendation"):
            value = raw_stay.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return "Flexible by preference"


def _summary_message(segments: List[CitySegment], itinerary: Dict) -> str:
    days = itinerary.get("days") if isinstance(itinerary, dict) else []
    if not isinstance(days, list):
        days = []

    cities_from_itinerary = itinerary.get("cities") if isinstance(itinerary, dict) else None
    if isinstance(cities_from_itinerary, list) and cities_from_itinerary:
        city_names = [str(c).strip() for c in cities_from_itinerary if str(c).strip()]
    else:
        city_names = [s.city for s in segments if s.city]

    total_days = itinerary.get("num_days") if isinstance(itinerary, dict) else None
    try:
        total_days = int(total_days)
    except Exception:
        total_days = len(days) if days else sum(max(1, s.days) for s in segments)
    if total_days <= 0:
        total_days = len(days) or 1

    if city_names:
        route_title = " + ".join(city_names[:2]) + (f" + {len(city_names) - 2} more" if len(city_names) > 2 else "")
    else:
        route_title = "India"

    lines: List[str] = [f"# ✈️ {total_days}-Day {route_title} Itinerary", ""]

    if not days:
        lines.append("I have generated your trip structure and saved it in the itinerary panel.")
        lines.append("Open the itinerary panel to review and refine each day.")
        return "\n".join(lines)

    for index, day in enumerate(days, start=1):
        if not isinstance(day, dict):
            continue
        day_number = day.get("day_number") or index
        city = str(day.get("city") or "Destination").strip()
        theme = str(day.get("theme") or city).strip()

        morning: List[str] = []
        afternoon: List[str] = []
        evening: List[str] = []

        day_budget = 0
        raw_stops = day.get("stops")
        stops = raw_stops if isinstance(raw_stops, list) else []
        for stop in stops:
            if not isinstance(stop, dict):
                continue
            bucket = _day_part(str(stop.get("time") or stop.get("arrival_time") or ""))
            text = _stop_line(stop)
            if bucket == "morning":
                morning.append(text)
            elif bucket == "evening":
                evening.append(text)
            else:
                afternoon.append(text)
            try:
                day_budget += int(stop.get("estimated_cost") or 0)
            except Exception:
                pass

        lines.append(f"## Day {day_number} - {theme}")
        lines.append(f"- Morning: {', '.join(morning) if morning else 'Slow start and local breakfast walk'}")
        lines.append(f"- Afternoon: {', '.join(afternoon) if afternoon else 'Core sightseeing and local experiences'}")
        lines.append(f"- Evening: {', '.join(evening) if evening else 'Relaxed dinner and easy night plan'}")
        lines.append(f"- Budget estimate: INR {max(day_budget, 0):,}")
        lines.append(f"- Stay suggestion: {_format_stay_hint(day.get('stay'))}")
        lines.append("")

    lines.append("If you want, I can now rebalance this for tighter budget, slower pace, or nightlife focus.")
    return "\n".join(lines).strip()


# Backward-compatible accessor used by chat.py
_orchestrator_instance: Optional[WatchoutOrchestrator] = None


def get_orchestrator() -> WatchoutOrchestrator:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = WatchoutOrchestrator()
    return _orchestrator_instance
