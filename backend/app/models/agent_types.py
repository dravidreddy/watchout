"""
Type definitions for agent orchestration system.
Provides TypedDict schemas for type safety and better IDE support.
"""
from typing import TypedDict, List, Optional, Dict, Any, Literal


class TravelPreferences(TypedDict, total=False):
    """User travel preferences extracted from conversation."""
    destinations: List[str]
    origin_city: Optional[str]
    duration_days: Optional[int]
    num_travelers: Optional[int]
    budget_range: Optional[str]  # "budget", "moderate", "luxury"
    travel_vibe: Optional[str]  # "adventure", "relaxation", "cultural", etc.
    preferred_activities: Optional[List[str]]
    dietary_restrictions: Optional[List[str]]
    accommodation_preferences: Optional[List[str]]
    transport_preferences: Optional[List[str]]


class UserMemory(TypedDict):
    """Structure for user memories from vector store."""
    user_id: str
    content: str
    type: str  # "preference", "past_trip", "feedback"
    metadata: Dict[str, Any]
    created_at: str
    score: Optional[float]  # Similarity score from vector search


class ConversationMessage(TypedDict):
    """Structure for conversation history messages."""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: Optional[str]
    metadata: Optional[Dict[str, Any]]


class AgentContext(TypedDict, total=False):
    """Context passed to individual agents."""
    preferences: TravelPreferences
    memories: List[UserMemory]
    conversation_history: List[ConversationMessage]
    city: Optional[str]
    budget: Optional[str]
    from_city: Optional[str]
    to_city: Optional[str]
    places_data: Optional[Dict[str, Any]]
    weather_data: Optional[Dict[str, Any]]
    extracted_preferences: Optional[TravelPreferences]


class OrchestrationPlan(TypedDict):
    """LLM-generated plan for agent orchestration."""
    agents: List[str]
    parallel: bool
    reasoning: str


class AgentResponse(TypedDict, total=False):
    """Standard response structure from agents."""
    response: str
    itinerary: Optional[Dict[str, Any]]
    raw_plan: Optional[Dict[str, Any]]
    weather: Optional[Dict[str, Any]]
    restaurants: Optional[List[Dict[str, Any]]]
    accommodations: Optional[List[Dict[str, Any]]]
    options: Optional[List[Dict[str, Any]]]
    route: Optional[Dict[str, Any]]
    extracted_preferences: Optional[TravelPreferences]
    is_complete: Optional[bool]


class StreamEvent(TypedDict, total=False):
    """SSE stream event structure."""
    type: Literal["status", "token", "tool_start", "tool_end", "data", "done", "error", "itinerary"]
    status: Optional[str]
    agent: Optional[str]
    content: Optional[str]
    tool_name: Optional[str]
    tool_output: Optional[Any]
    data_type: Optional[str]
    data: Optional[Any]
    is_complete: Optional[bool]
    trip_id: Optional[str]
    error: Optional[str]
    itinerary: Optional[Dict[str, Any]]
