"""
Itinerary generation and orchestration group.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.agents.clarification import ClarificationAgent as LegacyClarificationAgent
from app.agents.itinerary import ItineraryAgent
from app.agents.reviewer import ReviewerAgent
from app.agents.weather import WeatherAgent
from app.graph.compat import assemble_itinerary, summary_markdown
from app.graph.contracts import AgentResult, TripGraphState
from app.mcp.state import CitySegment


class ClarificationAgent:
    def __init__(self):
        self.agent = LegacyClarificationAgent()

    async def run(self, state: TripGraphState) -> AgentResult:
        missing = list(state.clarifications_needed)
        if not missing:
            return AgentResult(
                agent_id="itinerary_clarification",
                group="itinerary",
                status="skipped",
                confidence=0.8,
            )

        raw = await self.agent.run(
            state.message,
            context={
                "preferences": state.trip_constraints,
                "missing_fields": missing,
                "conversation_history": state.conversation_context,
            },
        )
        return AgentResult(
            agent_id="itinerary_clarification",
            group="itinerary",
            status="partial",
            confidence=0.6,
            open_questions=raw.get("missing_fields", []),
            recommendations={"assistant_message": raw.get("assistant_message", "")},
            state_delta={
                "clarifications_needed": raw.get("missing_fields", []),
                "preferences": raw.get("preferences", state.preferences),
                "ui_payloads": {
                    **state.ui_payloads,
                    "clarification_message": raw.get("assistant_message", ""),
                    "destination_suggestions": raw.get("destination_suggestions", []),
                },
            },
        )


class PlanningWeatherAgent:
    def __init__(self):
        self.agent = WeatherAgent()

    async def run(self, state: TripGraphState, segments: List[CitySegment]) -> AgentResult:
        weather_by_city: Dict[str, Any] = {}
        for seg in segments:
            raw = await self.agent.run(
                "",
                context={
                    "city": seg.city,
                    "preferences": {
                        **state.trip_constraints,
                        "destinations": [seg.city],
                    },
                },
            )
            weather_items = raw.get("data", {}).get("weather", [])
            weather_by_city[seg.city] = weather_items[0] if weather_items else raw.get("data", {})

        return AgentResult(
            agent_id="planning_weather",
            group="itinerary",
            confidence=0.68 if weather_by_city else 0.35,
            recommendations={"weather": weather_by_city},
            state_delta={
                "ui_payloads": {**state.ui_payloads, "weather": weather_by_city},
                "itinerary_plan": {**state.itinerary_plan, "weather": weather_by_city},
            },
        )


class ItineraryPlanningAgent:
    def __init__(self):
        self.agent = ItineraryAgent()

    async def run(self, state: TripGraphState, segments: List[CitySegment]) -> AgentResult:
        city_itineraries: List[Dict[str, Any]] = []
        for seg in segments:
            city_context = state.destination_experience_plan.get("cities", {}).get(seg.city, {})
            raw = await self.agent.run(
                "",
                context={
                    "preferences": {
                        **state.trip_constraints,
                        "destinations": [seg.city],
                        "duration_days": seg.days,
                        "origin_city": seg.arrives_from or state.trip_constraints.get("origin_city"),
                        "transport_preference": state.route_plan.get("transport", {}).get("primary_mode", seg.transport_preference),
                    },
                    "places_data": city_context,
                    "weather_data": state.ui_payloads.get("weather", {}).get(seg.city),
                    "timezone_id": state.trip_constraints.get("timezone_id", "UTC"),
                },
            )
            city_itineraries.append({
                "city": seg.city,
                "days": seg.days,
                **raw.get("data", {}),
            })

        full_itinerary = assemble_itinerary(
            segments=segments,
            city_itineraries=city_itineraries,
            intercity_routes=state.route_plan.get("legs", []),
            stays_by_city=state.destination_experience_plan.get("stays_by_city", {}),
            food_by_city=state.destination_experience_plan.get("food_by_city", {}),
            destination_experience_plan=state.destination_experience_plan,
            preferences=state.trip_constraints,
        )

        return AgentResult(
            agent_id="itinerary_planning",
            group="itinerary",
            confidence=0.78 if city_itineraries else 0.4,
            recommendations={"city_itineraries": city_itineraries},
            state_delta={
                "itinerary_plan": {
                    **full_itinerary,
                    "city_itineraries": city_itineraries,
                }
            },
        )


class ScheduleOptimizationAgent:
    def run(self, state: TripGraphState) -> AgentResult:
        itinerary = dict(state.itinerary_plan)
        days = itinerary.get("days", []) if isinstance(itinerary.get("days"), list) else []
        pace = str(state.trip_constraints.get("pace", "moderate")).lower()
        max_stops = {"relaxed": 3, "moderate": 4, "packed": 6}.get(pace, 4)
        warnings: List[str] = []

        for day in days:
            stops = day.get("stops") if isinstance(day.get("stops"), list) else []
            if len(stops) > max_stops:
                day["optional_stops"] = stops[max_stops:]
                day["stops"] = stops[:max_stops]
                warnings.append(
                    f"Day {day.get('day_number')} was trimmed to {max_stops} major stops for a {pace} pace."
                )

        itinerary["schedule_warnings"] = warnings
        return AgentResult(
            agent_id="schedule_optimization",
            group="itinerary",
            confidence=0.72,
            recommendations={"schedule_warnings": warnings},
            state_delta={"itinerary_plan": itinerary},
        )

    def repair(self, itinerary: Dict[str, Any], issues: List[str]) -> Dict[str, Any]:
        repaired = dict(itinerary)
        days = repaired.get("days", []) if isinstance(repaired.get("days"), list) else []
        for day in days:
            stops = day.get("stops") if isinstance(day.get("stops"), list) else []
            if len(stops) > 3:
                day["optional_stops"] = stops[3:]
                day["stops"] = stops[:3]
                day["notes"] = f"{day.get('notes', '')} Reviewer repair: trimmed overloaded schedule.".strip()
        repaired["reviewer_repairs"] = issues
        return repaired


class PersonalizationAgent:
    def run(self, state: TripGraphState) -> AgentResult:
        summary = {
            "route_strategy": state.route_plan.get("recommended_strategy"),
            "preferred_vibes": state.trip_constraints.get("travel_vibe", []),
            "interests": state.trip_constraints.get("interests", []),
            "budget_range": state.trip_constraints.get("budget_range"),
        }
        itinerary = dict(state.itinerary_plan)
        itinerary["personalization_summary"] = summary
        return AgentResult(
            agent_id="itinerary_personalization",
            group="itinerary",
            confidence=0.7,
            recommendations={"personalization_summary": summary},
            state_delta={"itinerary_plan": itinerary},
        )


class TripOptimizationAgent:
    def run(self, state: TripGraphState) -> AgentResult:
        itinerary = dict(state.itinerary_plan)
        days = itinerary.get("days", []) if isinstance(itinerary.get("days"), list) else []
        budget_total = 0
        for day in days:
            for stop in day.get("stops", []) if isinstance(day.get("stops"), list) else []:
                try:
                    budget_total += int(stop.get("estimated_cost") or 0)
                except Exception:
                    continue
        itinerary["budget_total"] = budget_total or itinerary.get("budget_total") or state.cost_model.get("estimated_total")
        itinerary["optimization"] = {
            "estimated_total": itinerary.get("budget_total"),
            "budget_target": state.cost_model.get("estimated_total"),
            "over_budget": bool(
                state.cost_model.get("estimated_total")
                and itinerary.get("budget_total")
                and itinerary.get("budget_total") > state.cost_model.get("estimated_total")
            ),
        }
        return AgentResult(
            agent_id="trip_optimization",
            group="itinerary",
            confidence=0.68,
            recommendations={"optimization": itinerary["optimization"]},
            state_delta={"itinerary_plan": itinerary},
        )


class FinalTripComposerAgent:
    def run(self, state: TripGraphState, segments: List[CitySegment]) -> AgentResult:
        itinerary = dict(state.itinerary_plan)
        markdown = summary_markdown(segments, itinerary)
        route_data = state.route_plan.get("legs", [])
        ui_payloads = {
            **state.ui_payloads,
            "itinerary": itinerary,
            "route": {"route_plan": state.route_plan, "legs": route_data},
            "response_markdown": markdown,
        }
        return AgentResult(
            agent_id="final_trip_composer",
            group="itinerary",
            confidence=0.8,
            recommendations={"response_markdown": markdown},
            state_delta={"ui_payloads": ui_payloads, "itinerary_plan": itinerary},
        )


class ItineraryOrchestrator:
    """Runs itinerary specialists and a reviewer loop."""

    def __init__(self):
        self.clarification = ClarificationAgent()
        self.weather = PlanningWeatherAgent()
        self.planning = ItineraryPlanningAgent()
        self.schedule = ScheduleOptimizationAgent()
        self.personalization = PersonalizationAgent()
        self.trip_optimization = TripOptimizationAgent()
        self.final = FinalTripComposerAgent()
        self.reviewer = ReviewerAgent()

    async def maybe_clarify(self, state: TripGraphState) -> AgentResult:
        return await self.clarification.run(state)

    async def run(self, state: TripGraphState, segments: List[CitySegment]) -> Tuple[List[AgentResult], Dict[str, Any]]:
        results: List[AgentResult] = []

        weather_result = await self.weather.run(state, segments)
        state.record_result(weather_result)
        results.append(weather_result)

        plan_result = await self.planning.run(state, segments)
        state.record_result(plan_result)
        results.append(plan_result)

        schedule_result = self.schedule.run(state)
        state.record_result(schedule_result)
        results.append(schedule_result)

        personalization_result = self.personalization.run(state)
        state.record_result(personalization_result)
        results.append(personalization_result)

        optimization_result = self.trip_optimization.run(state)
        state.record_result(optimization_result)
        results.append(optimization_result)

        review = await self.reviewer.review_itinerary(state.itinerary_plan)
        if not review.get("is_feasible", True):
            repaired = self.schedule.repair(state.itinerary_plan, review.get("issues", []))
            state.itinerary_plan = repaired
            second_review = await self.reviewer.review_itinerary(repaired)
            state.validation_issues.extend(review.get("issues", []))
            if not second_review.get("is_feasible", True):
                state.validation_issues.extend(second_review.get("issues", []))

        final_result = self.final.run(state, segments)
        state.record_result(final_result)
        results.append(final_result)

        return results, review
