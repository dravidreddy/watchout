"""
Route planning group orchestrator and specialist workers.
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.agents.route import RouteAgent
from app.agents.transportation import TransportationAgent
from app.graph.contracts import AgentResult, EvidenceRef, TripGraphState
from app.mcp.state import CitySegment
from app.tools.google_places import get_places_tool


class RouteOptimizationAgent:
    def __init__(self):
        self.route_agent = RouteAgent()

    async def run(self, state: TripGraphState, segments: List[CitySegment]) -> AgentResult:
        legs: List[Dict[str, Any]] = []
        evidence: List[EvidenceRef] = []

        for seg in segments:
            if not seg.arrives_from or seg.arrives_from == seg.city:
                continue
            raw = await self.route_agent.run(
                "",
                context={
                    "stops": [{"name": seg.arrives_from}, {"name": seg.city}],
                    "transport_preference": seg.transport_preference,
                },
            )
            data = raw.get("data", {})
            leg = {
                "from": seg.arrives_from,
                "to": seg.city,
                "transport_preference": seg.transport_preference,
                "travel_time_minutes": data.get("total_travel_time"),
                "distance_km": data.get("total_distance"),
                "route": data.get("route"),
            }
            legs.append(leg)
            evidence.append(EvidenceRef(
                source_type="agent",
                source_name="route_optimization",
                summary=f"Computed route from {seg.arrives_from} to {seg.city}",
                payload=leg,
                confidence=0.72,
                city=seg.city,
                trip_id=state.trip_id,
            ))

        return AgentResult(
            agent_id="route_optimization",
            group="route",
            confidence=0.72 if legs else 0.4,
            hard_constraints_checked=["destinations", "origin_city", "transport_preference"],
            evidence_refs=evidence,
            recommendations={"legs": legs},
            state_delta={
                "route_plan": {
                    "cities": [seg.city for seg in segments],
                    "legs": legs,
                }
            },
        )


class TransportationModePlanner:
    def __init__(self):
        self.transport_agent = TransportationAgent()

    async def run(self, state: TripGraphState) -> AgentResult:
        options_by_leg: List[Dict[str, Any]] = []
        primary_mode = None
        evidence: List[EvidenceRef] = []

        for leg in state.route_plan.get("legs", []):
            raw = await self.transport_agent.run(
                "",
                context={
                    "from_city": leg.get("from"),
                    "to_city": leg.get("to"),
                    "budget": state.trip_constraints.get("budget_range", "mid_range"),
                },
            )
            options = raw.get("data", {}).get("options", {})
            recommended_mode = options.get("recommended_mode") if isinstance(options, dict) else None
            entry = {
                "from": leg.get("from"),
                "to": leg.get("to"),
                "recommended_mode": recommended_mode or leg.get("transport_preference") or "flexible",
                "options": options,
            }
            if primary_mode is None:
                primary_mode = entry["recommended_mode"]
            options_by_leg.append(entry)
            evidence.append(EvidenceRef(
                source_type="agent",
                source_name="transportation_mode_planner",
                summary=f"Selected transport options for {leg.get('from')} to {leg.get('to')}",
                payload=entry,
                confidence=0.68,
                city=leg.get("to"),
                trip_id=state.trip_id,
            ))

        return AgentResult(
            agent_id="transportation_mode_planner",
            group="route",
            confidence=0.68 if options_by_leg else 0.4,
            evidence_refs=evidence,
            recommendations={"transport_options": options_by_leg},
            state_delta={
                "route_plan": {
                    **state.route_plan,
                    "transport": {
                        "options_by_leg": options_by_leg,
                        "primary_mode": primary_mode or state.trip_constraints.get("transport_preference", "flexible"),
                    },
                }
            },
        )


class ScenicRouteDiscoveryAgent:
    def __init__(self):
        self.route_agent = RouteAgent()

    async def run(self, state: TripGraphState) -> AgentResult:
        scenic_routes: List[Dict[str, Any]] = []
        road_trip_pref = str(state.trip_constraints.get("road_trip_preference", "")).lower()
        if "direct" in road_trip_pref:
            return AgentResult(
                agent_id="scenic_route_discovery",
                group="route",
                status="skipped",
                confidence=0.6,
                assumptions=["User requested direct routing; scenic detours were skipped."],
            )

        for leg in state.route_plan.get("legs", []):
            pitstops = await self.route_agent.discover_route_pitstops(
                str(leg.get("from", "")),
                str(leg.get("to", "")),
            )
            scenic_routes.append({
                "from": leg.get("from"),
                "to": leg.get("to"),
                "pitstops": pitstops[:4],
                "scenic_score": min(len(pitstops) / 4.0, 1.0),
            })

        return AgentResult(
            agent_id="scenic_route_discovery",
            group="route",
            confidence=0.65 if scenic_routes else 0.45,
            recommendations={"scenic_routes": scenic_routes},
            state_delta={"route_plan": {**state.route_plan, "scenic_routes": scenic_routes}},
        )


class StopoverExperienceAgent:
    def __init__(self):
        self.places = get_places_tool()

    async def run(self, state: TripGraphState) -> AgentResult:
        stopovers: List[Dict[str, Any]] = []

        for scenic in state.route_plan.get("scenic_routes", []):
            for pitstop in scenic.get("pitstops", [])[:3]:
                city = pitstop.get("name") or pitstop.get("city")
                attractions = await self.places.search_places(
                    f"top attractions in {city}",
                    place_type="tourist_attraction",
                ) if city else []
                stopovers.append({
                    "city": city,
                    "leg": f"{scenic.get('from')}->{scenic.get('to')}",
                    "reason": "Scenic or culturally interesting stopover on the route",
                    "attractions": attractions[:3],
                })

        return AgentResult(
            agent_id="stopover_experience",
            group="route",
            confidence=0.62 if stopovers else 0.4,
            recommendations={"stopovers": stopovers},
            state_delta={"route_plan": {**state.route_plan, "stopovers": stopovers}},
        )


class TravelLogisticsAgent:
    async def run(self, state: TripGraphState) -> AgentResult:
        total_minutes = 0
        warnings: List[str] = []
        for leg in state.route_plan.get("legs", []):
            minutes = int(leg.get("travel_time_minutes") or 0)
            total_minutes += max(0, minutes)
            if minutes >= 360:
                warnings.append(
                    f"{leg.get('from')} to {leg.get('to')} is a long transfer; add rest or overnight buffers."
                )
            if minutes >= 720:
                warnings.append(
                    f"{leg.get('from')} to {leg.get('to')} may be too long for the same day without fatigue."
                )

        return AgentResult(
            agent_id="travel_logistics",
            group="route",
            confidence=0.75,
            hard_constraints_checked=["travel_time", "transfer_feasibility"],
            recommendations={"warnings": warnings},
            state_delta={
                "route_plan": {
                    **state.route_plan,
                    "logistics": {
                        "total_travel_time_minutes": total_minutes,
                        "warnings": warnings,
                    },
                }
            },
        )


class RoutePersonalizationAgent:
    async def run(self, state: TripGraphState) -> AgentResult:
        vibes = state.trip_constraints.get("travel_vibe", [])
        if isinstance(vibes, str):
            vibes = [vibes]
        budget = state.trip_constraints.get("budget_range", "mid-range")
        strategy = "balanced"
        if any(v in {"adventure", "scenic", "romantic", "outdoors"} for v in vibes):
            strategy = "scenic"
        elif budget == "budget":
            strategy = "cost_aware"
        elif budget == "luxury":
            strategy = "comfort_first"

        note = {
            "strategy": strategy,
            "vibes": vibes,
            "budget": budget,
            "preferred_mode": state.route_plan.get("transport", {}).get("primary_mode", "flexible"),
        }

        return AgentResult(
            agent_id="route_personalization",
            group="route",
            confidence=0.7,
            recommendations={"personalization": note},
            state_delta={
                "route_plan": {
                    **state.route_plan,
                    "personalization": note,
                    "recommended_strategy": strategy,
                }
            },
        )


class RoutePlanningOrchestrator:
    """Runs the route-planning specialist group in dependency order."""

    def __init__(self):
        self.optimization = RouteOptimizationAgent()
        self.transportation = TransportationModePlanner()
        self.scenic = ScenicRouteDiscoveryAgent()
        self.stopovers = StopoverExperienceAgent()
        self.logistics = TravelLogisticsAgent()
        self.personalization = RoutePersonalizationAgent()

    async def run(self, state: TripGraphState, segments: List[CitySegment]) -> List[AgentResult]:
        results = [await self.optimization.run(state, segments)]
        state.record_result(results[-1])

        results.append(await self.transportation.run(state))
        state.record_result(results[-1])

        results.append(await self.scenic.run(state))
        state.record_result(results[-1])

        results.append(await self.stopovers.run(state))
        state.record_result(results[-1])

        results.append(await self.logistics.run(state))
        state.record_result(results[-1])

        results.append(await self.personalization.run(state))
        state.record_result(results[-1])

        return results
