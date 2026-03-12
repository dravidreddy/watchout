"""
Constraint resolution, conflict arbitration, and regeneration planning.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Set

from app.graph.contracts import TripGraphState

ROUTE_KEYS: Set[str] = {
    "destinations",
    "origin_city",
    "transport_preference",
    "road_trip_preference",
    "start_date",
    "end_date",
}

HOSPITALITY_KEYS: Set[str] = {
    "budget_range",
    "food_preferences",
    "interests",
    "travel_vibe",
}

ITINERARY_KEYS: Set[str] = {
    "duration_days",
    "num_travelers",
    "pace",
    "spontaneity",
    "special_requirements",
    "travel_style",
}


class ConstraintResolver:
    """Resolves cross-agent conflicts with a fixed precedence order."""

    def arbitrate(self, state: TripGraphState) -> TripGraphState:
        route_mode = state.route_plan.get("transport", {}).get("primary_mode")
        itinerary_mode = state.itinerary_plan.get("transport_summary", {}).get("mode")
        if route_mode and itinerary_mode and route_mode != itinerary_mode:
            state.conflicts.append({
                "type": "transport_mode_conflict",
                "winner": "route_plan",
                "loser": "itinerary_plan",
                "details": f"Using '{route_mode}' over itinerary mode '{itinerary_mode}'",
            })
            state.itinerary_plan.setdefault("transport_summary", {})["mode"] = route_mode

        route_cities = set(state.route_plan.get("cities", []))
        itinerary_cities = set(state.itinerary_plan.get("cities", []))
        if route_cities and itinerary_cities and not itinerary_cities.issubset(route_cities):
            state.conflicts.append({
                "type": "city_set_conflict",
                "winner": "route_plan",
                "loser": "itinerary_plan",
                "details": "Itinerary referenced cities that were not in the route plan.",
            })
            state.itinerary_plan["cities"] = sorted(route_cities | itinerary_cities)

        budget_total = state.cost_model.get("estimated_total")
        itinerary_budget = state.itinerary_plan.get("budget_total")
        if budget_total and itinerary_budget and itinerary_budget > budget_total:
            state.conflicts.append({
                "type": "budget_conflict",
                "winner": "budget_optimizer",
                "loser": "itinerary_plan",
                "details": "Itinerary budget exceeded the budget optimizer estimate.",
            })
            state.itinerary_plan["budget_total"] = budget_total

        return state


class RegenerationPlanner:
    """Determines which graph segments need regeneration for a refinement request."""

    def compute_scope(
        self,
        previous_preferences: Dict[str, Any],
        next_preferences: Dict[str, Any],
        user_message: str,
    ) -> List[str]:
        changed_keys = {
            key for key, value in (next_preferences or {}).items()
            if previous_preferences.get(key) != value
        }

        scope: List[str] = []
        if re.search(r"\bday\s+\d+\b", user_message.lower()):
            return ["itinerary"]
        if changed_keys & ROUTE_KEYS:
            scope.extend(["route", "hospitality", "itinerary"])
        elif changed_keys & HOSPITALITY_KEYS:
            scope.extend(["hospitality", "itinerary"])
        elif changed_keys & ITINERARY_KEYS:
            scope.append("itinerary")
        elif user_message.strip():
            scope.append("itinerary")
        return scope or ["itinerary"]

