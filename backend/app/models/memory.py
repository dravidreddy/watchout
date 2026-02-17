"""
Watchout Backend - Memory Models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MemoryType(str, Enum):
    """Types of memories stored for semantic retrieval."""
    
    PREFERENCE = "preference"  # User preferences from conversations
    TRIP_NOTE = "trip_note"  # Notes about past trips
    CONVERSATION = "conversation"  # Conversation excerpts
    FEEDBACK = "feedback"  # User feedback on suggestions
    CONSTRAINT = "constraint"  # User constraints (e.g., "I hate cold weather")


class MessageRole(str, Enum):
    """Roles in conversation."""
    
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """A single chat message."""
    
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Optional metadata
    agent_name: Optional[str] = None  # Which agent sent this
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_results: Optional[List[Dict[str, Any]]] = None


class Conversation(BaseModel):
    """Conversation thread for a trip."""
    
    trip_id: str
    user_id: str
    
    messages: List[ChatMessage] = Field(default_factory=list)
    
    # Agent state
    current_agent: Optional[str] = None
    agent_state: Optional[Dict[str, Any]] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Memory(BaseModel):
    """Semantic memory stored for RAG retrieval."""
    
    user_id: str
    type: MemoryType
    content: str
    
    # Embedding (stored separately in MongoDB)
    # embedding: List[float] - not included in Pydantic model
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Source
    source_trip_id: Optional[str] = None
    source_conversation_id: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MemoryCreate(BaseModel):
    """Model for creating a new memory."""
    type: MemoryType
    content: str
    metadata: Optional[Dict[str, Any]] = None
    source_trip_id: Optional[str] = None


class MemorySearchResult(BaseModel):
    """Search result from vector search."""
    content: str
    type: MemoryType
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ConversationCreate(BaseModel):
    """Model for creating a new conversation."""
    trip_id: str


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str
    trip_id: Optional[str] = None
    
    # Optional context
    include_memories: bool = True
    max_memories: int = 5


class ChatStreamEvent(BaseModel):
    """Event sent during SSE streaming."""
    
    event_type: str  # "token", "status", "tool_start", "tool_end", "error", "done"
    
    # For token events
    content: Optional[str] = None
    
    # For status updates
    status: Optional[str] = None
    agent: Optional[str] = None
    
    # For tool events
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_output: Optional[Dict[str, Any]] = None
    
    # For errors
    error: Optional[str] = None
