"""
Compatibility helpers for assembling user-facing itinerary payloads.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from app.mcp.state import CitySegment


def assemble_itinerary(
    segments: List[CitySegment],
    city_itineraries: List[Dict[str, Any]],
    intercity_routes: List[Dict[str, Any]],
    stays_by_city: Dict[str, Any],
    food_by_city: Dict[str, Any],
    destination_experience_plan: Dict[str, Any],
    preferences: Dict[str, Any],
) -> Dict[str, Any]:
    """Merge city-level outputs into the existing frontend itinerary shape."""
    cities = [seg.city for seg in segments]
    total_days = sum(seg.days for seg in segments)

    all_days: List[Dict[str, Any]] = []
    day_counter = 1
    for itin in city_itineraries:
        city_name = itin.get("city", "")
        raw_plan = itin.get("raw_plan", {})
        itin_obj = itin.get("itinerary", {})

        raw_days: List[Dict[str, Any]] = []
        if isinstance(itin_obj, dict) and "days" in itin_obj:
            raw_days = itin_obj["days"]
        elif hasattr(itin_obj, "days") and isinstance(itin_obj.days, list):
            raw_days = [d.dict() if hasattr(d, "dict") else d for d in itin_obj.days]
        elif isinstance(raw_plan, dict) and "days" in raw_plan:
            raw_days = raw_plan.get("days", [])

        for day in raw_days if isinstance(raw_days, list) else []:
            if hasattr(day, "dict"):
                day = day.dict()
            if not isinstance(day, dict):
                continue
            city_plan = destination_experience_plan.get("cities", {}).get(city_name, {})
            all_days.append({
                **day,
                "day_number": day_counter,
                "city": city_name,
                "stay": stays_by_city.get(city_name, {}).get("recommendation"),
                "food_spots": food_by_city.get(city_name, {}).get("restaurants", []),
                "destination_highlights": city_plan.get("highlights", []),
            })
            day_counter += 1

    budget_range = preferences.get("budget_range", "mid-range")
    budget_total: Optional[int] = None
    if budget_range == "budget":
        budget_total = total_days * 2000
    elif budget_range == "luxury":
        budget_total = total_days * 12000
    else:
        budget_total = total_days * 5000

    return {
        "title": f"{' -> '.join(cities)} Trip",
        "cities": cities,
        "num_days": total_days,
        "num_travelers": preferences.get("num_travelers", 1),
        "start_date": preferences.get("start_date"),
        "end_date": preferences.get("end_date"),
        "budget_range": budget_range,
        "budget_total": budget_total,
        "days": all_days,
        "city_segments": [
            {
                **itin,
                "stays": stays_by_city.get(itin.get("city", ""), {}),
                "food": food_by_city.get(itin.get("city", ""), {}),
                "destination_experience": destination_experience_plan.get("cities", {}).get(itin.get("city", ""), {}),
            }
            for itin in city_itineraries
        ],
        "intercity_routes": intercity_routes,
        "summary": f"A {total_days}-day adventure across {', '.join(cities)}.",
    }


def summary_markdown(segments: List[CitySegment], itinerary: Dict[str, Any]) -> str:
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

    route_title = " + ".join(city_names[:2]) + (f" + {len(city_names) - 2} more" if len(city_names) > 2 else "") if city_names else "India"
    lines: List[str] = [f"# Trip Plan: {total_days}-Day {route_title} Itinerary", ""]

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
        stops = day.get("stops") if isinstance(day.get("stops"), list) else []
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


def _extract_hour(time_text: str) -> Optional[int]:
    match = re.search(r"(\d{1,2})", time_text or "")
    if not match:
        return None
    hour = int(match.group(1))
    return hour if 0 <= hour <= 23 else None


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
    return f"{name} ({'; '.join(details)})" if details else name


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
