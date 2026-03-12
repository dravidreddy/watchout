"""
Executive supervisor for the graph-based travel planning runtime.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.agents.hospitality_group import HospitalityOrchestrator
from app.agents.itinerary_group import ItineraryOrchestrator
from app.agents.route_group import RoutePlanningOrchestrator
from app.graph.arbitration import ConstraintResolver, RegenerationPlanner
from app.graph.contracts import AgentResult, TripGraphState
from app.graph.memory import GraphMemoryManager
from app.graph.persistence import GraphPersistence
from app.mcp.state import TripStateMachine

logger = logging.getLogger(__name__)


class ConstraintUpdateAgent(BaseAgent):
    """Extracts explicit refinement or preference updates from a user message."""

    def __init__(self):
        super().__init__(
            name="Constraint Update Extractor",
            description="Extract explicit preference updates or refinement intent from user follow-up messages.",
            model_type="fast",
        )

    async def run(self, user_input: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        context = context or {}
        current = context.get("preferences", {})
        if not user_input.strip():
            return {"response": "", "data": {"intent": "plan_trip", "preferences": {}, "day_targets": []}, "error": None}

        prompt = (
            "Extract only explicit trip refinements from the latest user message.\n"
            "Do not infer missing fields.\n"
            f"Current preferences: {current}\n"
            f"Latest message: {user_input}\n"
            "Return intent as one of: confirm, refine_trip, answer_question, plan_trip.\n"
            "If the user mentions a specific day, include it in day_targets.\n"
            "Only include preference keys that were clearly changed."
        )
        schema = {
            "type": "object",
            "properties": {
                "intent": {"type": "string"},
                "preferences": {
                    "type": "object",
                    "properties": {
                        "destinations": {"type": "array", "items": {"type": "string"}},
                        "origin_city": {"type": "string"},
                        "duration_days": {"type": "integer"},
                        "num_travelers": {"type": "integer"},
                        "budget_range": {"type": "string"},
                        "travel_vibe": {"type": "array", "items": {"type": "string"}},
                        "pace": {"type": "string"},
                        "transport_preference": {"type": "string"},
                        "road_trip_preference": {"type": "string"},
                        "food_preferences": {"type": "array", "items": {"type": "string"}},
                        "interests": {"type": "array", "items": {"type": "string"}},
                        "special_requirements": {"type": "string"},
                        "start_date": {"type": "string"},
                        "end_date": {"type": "string"},
                    },
                },
                "day_targets": {"type": "array", "items": {"type": "string"}},
                "confidence": {"type": "number"},
            },
            "required": ["intent", "preferences", "day_targets", "confidence"],
        }
        try:
            parsed = await self.generate_structured(prompt, schema) or {}
            return {"response": "", "data": parsed, "error": None}
        except Exception as exc:
            logger.warning("Constraint update extraction failed: %s", exc)
            return {
                "response": "",
                "data": {"intent": "refine_trip", "preferences": {}, "day_targets": [], "confidence": 0.3},
                "error": str(exc),
            }


class ExecutiveTripSupervisor:
    """Single planning entrypoint for the next-generation graph runtime."""

    def __init__(self):
        self.memory = GraphMemoryManager()
        self.persistence = GraphPersistence()
        self.resolver = ConstraintResolver()
        self.regeneration = RegenerationPlanner()
        self.update_agent = ConstraintUpdateAgent()
        self.route_group = RoutePlanningOrchestrator()
        self.hospitality_group = HospitalityOrchestrator()
        self.itinerary_group = ItineraryOrchestrator()

    async def run(
        self,
        *,
        user_id: str,
        trip_id: str,
        message: str,
        trip_context: Dict[str, Any],
        conversation_history: List[Dict[str, Any]],
        trip_state_machine: TripStateMachine,
    ) -> TripGraphState:
        state = TripGraphState.from_runtime(
            user_id=user_id,
            trip_id=trip_id,
            message=message,
            phase=trip_state_machine.state.value,
            trip_context=trip_context,
            conversation_history=conversation_history,
        )

        await self.memory.hydrate(state)

        previous_preferences = dict(state.confirmed_trip_constraints)
        update_raw = await self.update_agent.run(
            message,
            context={"preferences": state.trip_constraints},
        )
        update_data = update_raw.get("data", {})
        state.set_intent(update_data.get("intent", "plan_trip"))
        state.latest_user_preferences = update_data.get("preferences", {}) or {}
        state.session_memory["day_targets"] = update_data.get("day_targets", [])

        merged_preferences, _ = self.memory.apply_preference_update(
            current=state.confirmed_trip_constraints,
            updates=state.latest_user_preferences,
            user_message=message,
        )
        state.confirmed_trip_constraints = merged_preferences
        state.preferences = merged_preferences
        state.trip_constraints = self.memory.resolve_constraints(state)

        state.regeneration_scope = self.regeneration.compute_scope(
            previous_preferences=previous_preferences,
            next_preferences=state.trip_constraints,
            user_message=message,
        )

        refreshed_sm = trip_state_machine.merge_preferences(state.trip_constraints)
        if refreshed_sm.missing_fields:
            state.clarifications_needed = list(refreshed_sm.missing_fields)
        if state.clarifications_needed:
            clarify_result = await self.itinerary_group.maybe_clarify(state)
            state.record_result(clarify_result)
            await self._persist_result(state, clarify_result)
            return state

        segments = refreshed_sm.build_segments()

        if "route" in state.regeneration_scope or not state.route_plan:
            for result in await self.route_group.run(state, segments):
                await self._persist_result(state, result)

        if "hospitality" in state.regeneration_scope or not state.destination_experience_plan:
            for result in await self.hospitality_group.run(state):
                await self._persist_result(state, result)

        if "itinerary" in state.regeneration_scope or not state.itinerary_plan:
            itinerary_results, review = await self.itinerary_group.run(state, segments)
            for result in itinerary_results:
                await self._persist_result(state, result)
            if not review.get("is_feasible", True):
                state.validation_issues.extend(review.get("issues", []))

        state.locked_logistics = {
            "transport_preference": state.route_plan.get("transport", {}).get("primary_mode"),
        }
        state.trip_constraints = self.memory.resolve_constraints(state)
        self.resolver.arbitrate(state)
        return state

    async def _persist_result(self, state: TripGraphState, result: AgentResult) -> None:
        await self.persistence.persist_agent_result(state, result)
        if result.evidence_refs:
            await self.persistence.persist_evidence(state, result.evidence_refs)
