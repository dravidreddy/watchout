"""
Watchout Backend - Data Models
"""
from app.models.user import (
    UserProfile,
    UserPreferences,
    UserCreate,
    UserUpdate,
    UserResponse,
    TravelStyle,
    TravelVibe,
    PacePreference,
    BudgetRange
)
from app.models.trip import (
    Trip,
    TripCreate,
    TripUpdate,
    TripResponse,
    TripStatus,
    Itinerary,
    DayPlan,
    ActivityStop,
    TransportLeg,
    TransportMode,
    AccommodationDetails
)
from app.models.memory import (
    Memory,
    MemoryCreate,
    MemoryType,
    MemorySearchResult,
    Conversation,
    ConversationCreate,
    ChatMessage,
    MessageRole,
    ChatRequest,
    ChatStreamEvent
)

__all__ = [
    # User models
    "UserProfile",
    "UserPreferences",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "TravelStyle",
    "TravelVibe",
    "PacePreference",
    "BudgetRange",
    
    # Trip models
    "Trip",
    "TripCreate",
    "TripUpdate",
    "TripResponse",
    "TripStatus",
    "Itinerary",
    "DayPlan",
    "ActivityStop",
    "TransportLeg",
    "TransportMode",
    "AccommodationDetails",
    
    # Memory models
    "Memory",
    "MemoryCreate",
    "MemoryType",
    "MemorySearchResult",
    "Conversation",
    "ConversationCreate",
    "ChatMessage",
    "MessageRole",
    "ChatRequest",
    "ChatStreamEvent"
]
