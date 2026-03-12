"""
Hospitality and destination-experience group orchestrator.
"""
from __future__ import annotations

from typing import Any, Dict, List, Set

from app.agents.food import FoodAgent
from app.agents.stay import StayAgent
from app.graph.contracts import AgentResult, EvidenceRef, TripGraphState
from app.tools.google_places import get_places_tool
from app.tools.serper_search import get_serper_tool
from app.tools.tavily_search import get_tavily_tool


class AccommodationAgent:
    def __init__(self):
        self.agent = StayAgent()

    async def run(self, state: TripGraphState, cities: List[str]) -> AgentResult:
        by_city: Dict[str, Any] = {}
        evidence: List[EvidenceRef] = []
        for city in cities:
            raw = await self.agent.run(
                "",
                context={
                    "city": city,
                    "budget": state.trip_constraints.get("budget_range", "mid_range"),
                    "preferences": state.trip_constraints,
                },
            )
            city_plan = raw.get("data", {}).get("accommodations", {})
            by_city[city] = city_plan
            evidence.append(EvidenceRef(
                source_type="agent",
                source_name="accommodation",
                summary=f"Accommodation options for {city}",
                payload=city_plan if isinstance(city_plan, dict) else {"value": city_plan},
                confidence=0.7,
                city=city,
                trip_id=state.trip_id,
            ))

        return AgentResult(
            agent_id="accommodation",
            group="hospitality",
            confidence=0.7 if by_city else 0.4,
            evidence_refs=evidence,
            recommendations={"stays": by_city},
            state_delta={
                "destination_experience_plan": {
                    **state.destination_experience_plan,
                    "cities": {
                        **state.destination_experience_plan.get("cities", {}),
                        **{city: {"stays": data} for city, data in by_city.items()},
                    },
                    "stays_by_city": by_city,
                }
            },
        )


class RestaurantFoodAgent:
    def __init__(self):
        self.agent = FoodAgent()

    async def run(self, state: TripGraphState, cities: List[str]) -> AgentResult:
        by_city: Dict[str, Any] = {}
        for city in cities:
            raw = await self.agent.run("", context={"city": city, "preferences": state.trip_constraints})
            by_city[city] = raw.get("data", {})

        city_payload = {}
        for city, data in by_city.items():
            city_payload[city] = {
                **state.destination_experience_plan.get("cities", {}).get(city, {}),
                "food": data,
            }

        return AgentResult(
            agent_id="restaurant_food",
            group="hospitality",
            confidence=0.7 if by_city else 0.4,
            recommendations={"food": by_city},
            state_delta={
                "destination_experience_plan": {
                    **state.destination_experience_plan,
                    "cities": {
                        **state.destination_experience_plan.get("cities", {}),
                        **city_payload,
                    },
                    "food_by_city": by_city,
                }
            },
        )


class AdventureActivitiesAgent:
    def __init__(self):
        self.places = get_places_tool()
        self.tavily = get_tavily_tool()

    async def run(self, state: TripGraphState, cities: List[str]) -> AgentResult:
        by_city: Dict[str, Any] = {}
        for city in cities:
            places = await self.places.search_places(
                f"adventure activities in {city}",
                place_type="tourist_attraction",
            )
            tips = await self.tavily.search_travel_info(city, topic="adventure activities") if city else None
            by_city[city] = {
                "places": places[:5],
                "research_summary": (tips or {}).get("answer"),
            }

        merged = {
            city: {
                **state.destination_experience_plan.get("cities", {}).get(city, {}),
                "activities": data,
            }
            for city, data in by_city.items()
        }
        return AgentResult(
            agent_id="adventure_activities",
            group="hospitality",
            confidence=0.62 if by_city else 0.35,
            recommendations={"activities": by_city},
            state_delta={
                "destination_experience_plan": {
                    **state.destination_experience_plan,
                    "cities": {
                        **state.destination_experience_plan.get("cities", {}),
                        **merged,
                    },
                }
            },
        )


class DestinationExplorationAgent:
    def __init__(self):
        self.places = get_places_tool()
        self.serper = get_serper_tool()

    async def run(self, state: TripGraphState, cities: List[str]) -> AgentResult:
        by_city: Dict[str, Any] = {}
        for city in cities:
            attractions = await self.places.search_places(
                f"top attractions in {city}",
                place_type="tourist_attraction",
            )
            local_search = await self.serper.search_places("hidden gems", city)
            by_city[city] = {
                "highlights": attractions[:6],
                "hidden_gems": (local_search or {}).get("places", [])[:4],
            }

        merged = {
            city: {
                **state.destination_experience_plan.get("cities", {}).get(city, {}),
                "exploration": data,
                "highlights": data.get("highlights", []),
            }
            for city, data in by_city.items()
        }
        return AgentResult(
            agent_id="destination_exploration",
            group="hospitality",
            confidence=0.66 if by_city else 0.4,
            recommendations={"exploration": by_city},
            state_delta={
                "destination_experience_plan": {
                    **state.destination_experience_plan,
                    "cities": {
                        **state.destination_experience_plan.get("cities", {}),
                        **merged,
                    },
                }
            },
        )


class BudgetOptimizationAgent:
    async def run(self, state: TripGraphState, cities: List[str]) -> AgentResult:
        multiplier = {"budget": 2500, "mid_range": 6000, "mid-range": 6000, "luxury": 15000}.get(
            str(state.trip_constraints.get("budget_range", "mid_range")).lower(),
            6000,
        )
        num_days = int(state.trip_constraints.get("duration_days") or len(cities) or 1)
        estimated_total = multiplier * max(1, num_days)
        budget = {
            "estimated_daily_budget": multiplier,
            "estimated_total": estimated_total,
            "budget_range": state.trip_constraints.get("budget_range", "mid_range"),
        }
        return AgentResult(
            agent_id="budget_optimization",
            group="hospitality",
            confidence=0.64,
            recommendations={"budget": budget},
            state_delta={
                "destination_experience_plan": {
                    **state.destination_experience_plan,
                    "budget": budget,
                },
                "cost_model": budget,
            },
        )


class ExperiencePersonalizationAgent:
    async def run(self, state: TripGraphState, cities: List[str]) -> AgentResult:
        vibes = state.trip_constraints.get("travel_vibe", [])
        if isinstance(vibes, str):
            vibes = [vibes]
        interests = state.trip_constraints.get("interests", [])
        highlights_by_city: Dict[str, Any] = {}
        for city in cities:
            city_plan = state.destination_experience_plan.get("cities", {}).get(city, {})
            highlights = city_plan.get("highlights", [])[:3]
            highlights_by_city[city] = {
                "preferred_vibes": vibes,
                "interests": interests,
                "selected_highlights": highlights,
            }

        merged = {
            city: {
                **state.destination_experience_plan.get("cities", {}).get(city, {}),
                "personalization": data,
            }
            for city, data in highlights_by_city.items()
        }
        return AgentResult(
            agent_id="experience_personalization",
            group="hospitality",
            confidence=0.7,
            recommendations={"personalization": highlights_by_city},
            state_delta={
                "destination_experience_plan": {
                    **state.destination_experience_plan,
                    "cities": {
                        **state.destination_experience_plan.get("cities", {}),
                        **merged,
                    },
                }
            },
        )


class HospitalityOrchestrator:
    """Runs hospitality specialists in dependency order."""

    def __init__(self):
        self.accommodation = AccommodationAgent()
        self.food = RestaurantFoodAgent()
        self.activities = AdventureActivitiesAgent()
        self.exploration = DestinationExplorationAgent()
        self.budget = BudgetOptimizationAgent()
        self.personalization = ExperiencePersonalizationAgent()

    def _target_cities(self, state: TripGraphState) -> List[str]:
        cities: Set[str] = set(state.route_plan.get("cities", []))
        for stopover in state.route_plan.get("stopovers", [])[:2]:
            city = stopover.get("city")
            if city:
                cities.add(city)
        if not cities:
            for destination in state.trip_constraints.get("destinations", []):
                if destination:
                    cities.add(destination)
        return sorted(cities)

    async def run(self, state: TripGraphState) -> List[AgentResult]:
        cities = self._target_cities(state)
        results = [await self.accommodation.run(state, cities)]
        state.record_result(results[-1])

        results.append(await self.food.run(state, cities))
        state.record_result(results[-1])

        results.append(await self.activities.run(state, cities))
        state.record_result(results[-1])

        results.append(await self.exploration.run(state, cities))
        state.record_result(results[-1])

        results.append(await self.budget.run(state, cities))
        state.record_result(results[-1])

        results.append(await self.personalization.run(state, cities))
        state.record_result(results[-1])

        return results
