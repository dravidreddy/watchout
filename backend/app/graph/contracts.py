"""
Shared contracts for the graph-based travel planning runtime.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EvidenceRef(BaseModel):
    """Normalised evidence reference captured from tools, memory, or agents."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    evidence_id: str = Field(default_factory=lambda: uuid4().hex)
    source_type: Literal["tool", "agent", "memory", "derived"] = "derived"
    source_name: str
    summary: str = ""
    payload: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.5
    city: Optional[str] = None
    trip_id: Optional[str] = None
    created_at: datetime = Field(default_factory=_utcnow)


class AgentResult(BaseModel):
    """Canonical result emitted by all graph workers."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    agent_id: str
    group: str
    status: Literal["success", "partial", "error", "skipped"] = "success"
    confidence: float = 0.5
    assumptions: List[str] = Field(default_factory=list)
    evidence_refs: List[EvidenceRef] = Field(default_factory=list)
    hard_constraints_checked: List[str] = Field(default_factory=list)
    recommendations: Dict[str, Any] = Field(default_factory=dict)
    open_questions: List[str] = Field(default_factory=list)
    state_delta: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_utcnow)


class TripGraphState(BaseModel):
    """Typed shared state flowing through the graph runtime."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    request_id: str = Field(default_factory=lambda: uuid4().hex)
    user_id: str
    trip_id: str
    phase: str = "planning"
    message: str = ""
    intent: str = "plan_trip"
    conversation_context: List[Dict[str, Any]] = Field(default_factory=list)
    user_profile: Dict[str, Any] = Field(default_factory=dict)
    profile_preferences: Dict[str, Any] = Field(default_factory=dict)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    latest_user_preferences: Dict[str, Any] = Field(default_factory=dict)
    confirmed_trip_constraints: Dict[str, Any] = Field(default_factory=dict)
    locked_logistics: Dict[str, Any] = Field(default_factory=dict)
    inferred_preferences: Dict[str, Any] = Field(default_factory=dict)
    session_memory: Dict[str, Any] = Field(default_factory=dict)
    profile_memory: Dict[str, Any] = Field(default_factory=dict)
    trip_memory: Dict[str, Any] = Field(default_factory=dict)
    trip_constraints: Dict[str, Any] = Field(default_factory=dict)
    clarifications_needed: List[str] = Field(default_factory=list)
    route_plan: Dict[str, Any] = Field(default_factory=dict)
    destination_experience_plan: Dict[str, Any] = Field(default_factory=dict)
    itinerary_plan: Dict[str, Any] = Field(default_factory=dict)
    cost_model: Dict[str, Any] = Field(default_factory=dict)
    evidence_refs: List[EvidenceRef] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    validation_issues: List[str] = Field(default_factory=list)
    confidence: Dict[str, float] = Field(default_factory=dict)
    ui_payloads: Dict[str, Any] = Field(default_factory=dict)
    regeneration_scope: List[str] = Field(default_factory=list)
    rejected_options: List[Dict[str, Any]] = Field(default_factory=list)
    agent_results: Dict[str, AgentResult] = Field(default_factory=dict)
    feature_flags: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_utcnow)

    @classmethod
    def from_runtime(
        cls,
        *,
        user_id: str,
        trip_id: str,
        message: str,
        phase: str,
        trip_context: Dict[str, Any],
        conversation_history: List[Dict[str, Any]],
    ) -> "TripGraphState":
        preferences = dict(trip_context.get("preferences") or {})
        profile_preferences = dict(trip_context.get("profile_preferences") or {})
        itinerary = trip_context.get("itinerary")
        route_plan = trip_context.get("route_plan") or {}
        destination_experience_plan = trip_context.get("destination_experience_plan") or {}
        cost_model = trip_context.get("cost_model") or {}
        return cls(
            user_id=user_id,
            trip_id=trip_id,
            phase=phase,
            message=message,
            conversation_context=conversation_history[-30:],
            user_profile=profile_preferences,
            profile_preferences=profile_preferences,
            preferences=preferences,
            confirmed_trip_constraints=dict(preferences),
            trip_memory={"existing_itinerary": itinerary} if itinerary else {},
            route_plan=dict(route_plan),
            destination_experience_plan=dict(destination_experience_plan),
            cost_model=dict(cost_model),
            itinerary_plan=dict(itinerary) if isinstance(itinerary, dict) else {},
            feature_flags=dict(trip_context.get("feature_flags") or {}),
        )

    def record_result(self, result: AgentResult) -> None:
        """Persist result into shared state and merge its key outputs."""
        self.agent_results[result.agent_id] = result
        self.assumptions.extend([a for a in result.assumptions if a not in self.assumptions])
        self.evidence_refs.extend(result.evidence_refs)
        self.confidence[result.agent_id] = result.confidence
        if result.open_questions:
            for question in result.open_questions:
                if question not in self.clarifications_needed:
                    self.clarifications_needed.append(question)
        if result.errors:
            self.validation_issues.extend([e for e in result.errors if e not in self.validation_issues])
        if result.state_delta:
            self._merge_state_delta(result.state_delta)

    def _merge_state_delta(self, delta: Dict[str, Any]) -> None:
        for key, value in delta.items():
            current = getattr(self, key, None)
            if isinstance(current, dict) and isinstance(value, dict):
                setattr(self, key, {**current, **value})
            elif isinstance(current, list) and isinstance(value, list):
                setattr(self, key, current + value)
            else:
                setattr(self, key, value)

    def set_intent(self, intent: str) -> None:
        self.intent = intent
