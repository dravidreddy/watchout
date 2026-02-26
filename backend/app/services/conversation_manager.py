"""
Watchout Backend - Conversation Manager Service

Handles conversation persistence and context management.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

from app.db.mongo import conversations_collection, trips_collection, MongoDB
from app.db.vector_store import VectorStore


class ConversationManager:
    """
    Central service for managing conversations and context.
    
    Responsibilities:
    - Save user and assistant messages
    - Retrieve conversation history
    - Build context for agents with history and preferences
    - Store important interactions as memories
    """
    
    @classmethod
    async def save_message(
        cls,
        trip_id: str,
        user_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save a message to the conversation history.
        
        Args:
            trip_id: The trip this conversation belongs to
            user_id: User's Firebase UID
            role: "user" or "assistant"
            content: Message content
            metadata: Additional data (agents used, structured data, etc.)
        
        Returns:
            The conversation document ID
        """
        convos = conversations_collection()
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc),
            "metadata": metadata or {}
        }
        
        # Upsert: create conversation if doesn't exist, append message if exists
        result = await convos.update_one(
            {"trip_id": trip_id, "user_id": user_id},
            {
                "$push": {"messages": message},
                "$set": {"updated_at": datetime.now(timezone.utc)},
                "$setOnInsert": {
                    "trip_id": trip_id,
                    "user_id": user_id,
                    "created_at": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )
        
        return str(result.upserted_id or trip_id)
    
    @classmethod
    async def save_message_pair(
        cls,
        trip_id: str,
        user_id: str,
        user_message: str,
        assistant_message: str,
        assistant_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save user and assistant message pair atomically using MongoDB transactions.
        
        This ensures that either both messages are saved or neither is saved,
        preventing conversation history corruption when errors occur mid-stream.
        
        Args:
            trip_id: The trip this conversation belongs to
            user_id: User's Firebase UID
            user_message: The user's message
            assistant_message: The assistant's response
            assistant_metadata: Additional data for assistant message
        
        Returns:
            True if both messages were saved successfully
        """
        client = MongoDB.client
        if not client:
            # Fallback to non-transactional if client not available
            await cls.save_message(trip_id, user_id, "user", user_message)
            await cls.save_message(trip_id, user_id, "assistant", assistant_message, assistant_metadata)
            return True
        
        # Start a client session for the transaction
        async with await client.start_session() as session:
            async with session.start_transaction():
                convos = conversations_collection()
                
                user_msg = {
                    "role": "user",
                    "content": user_message,
                    "timestamp": datetime.now(timezone.utc),
                    "metadata": {}
                }
                
                assistant_msg = {
                    "role": "assistant",
                    "content": assistant_message,
                    "timestamp": datetime.now(timezone.utc),
                    "metadata": assistant_metadata or {}
                }
                
                # Push both messages atomically
                await convos.update_one(
                    {"trip_id": trip_id, "user_id": user_id},
                    {
                        "$push": {
                            "messages": {
                                "$each": [user_msg, assistant_msg]
                            }
                        },
                        "$set": {"updated_at": datetime.now(timezone.utc)},
                        "$setOnInsert": {
                            "trip_id": trip_id,
                            "user_id": user_id,
                            "created_at": datetime.now(timezone.utc)
                        }
                    },
                    upsert=True,
                    session=session
                )
        
        return True
    
    @classmethod
    async def get_history(
        cls,
        trip_id: str,
        user_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get recent conversation history.
        
        Args:
            trip_id: The trip ID
            user_id: User's Firebase UID
            limit: Maximum messages to return
        
        Returns:
            List of messages (most recent last)
        """
        convos = conversations_collection()
        
        conversation = await convos.find_one(
            {"trip_id": trip_id, "user_id": user_id},
            {"messages": {"$slice": -limit}}  # Get last N messages
        )
        
        if not conversation:
            return []
        
        messages = conversation.get("messages", [])
        
        # Convert timestamps to strings for JSON serialization
        for msg in messages:
            if isinstance(msg.get("timestamp"), datetime):
                msg["timestamp"] = msg["timestamp"].isoformat()
        
        return messages
    
    @classmethod
    async def build_agent_context(
        cls,
        trip_id: str,
        user_id: str,
        current_message: str,
        include_history: bool = True,
        history_limit: int = 10
    ) -> Dict[str, Any]:
        """
        Build comprehensive context for agents.
        
        Combines:
        - Conversation history
        - Trip preferences
        - Relevant memories from vector store
        
        Args:
            trip_id: The trip ID
            user_id: User's Firebase UID
            current_message: The current user message
            include_history: Whether to include conversation history
            history_limit: How many past messages to include
        
        Returns:
            Context dictionary for agents
        """
        context = {
            "user_id": user_id,
            "trip_id": trip_id,
            "preferences": {},
            "conversation_history": [],
            "memories": [],
            "itinerary": None
        }
        
        # 1. Get trip preferences
        try:
            trips = trips_collection()
            trip = await trips.find_one({"_id": trip_id, "user_id": user_id})
            if trip:
                context["preferences"] = trip.get("preferences", {})
                context["itinerary"] = trip.get("itinerary")
        except Exception as e:
            logger.warning("Error loading trip: %s", e)
        
        # 2. Get conversation history
        if include_history:
            try:
                context["conversation_history"] = await cls.get_history(
                    trip_id, user_id, limit=history_limit
                )
            except Exception as e:
                logger.warning("Error loading history: %s", e)
        
        # 3. Get relevant memories
        try:
            memories = await VectorStore.search_memories(
                user_id, current_message, limit=5
            )
            context["memories"] = [
                {"content": m.get("content"), "type": m.get("type")}
                for m in memories
            ]
        except Exception as e:
            logger.warning("Error loading memories: %s", e)
        
        return context
    
    @classmethod
    async def store_preference_memory(
        cls,
        user_id: str,
        preference_content: str,
        preference_type: str = "preference"
    ) -> str:
        """
        Store a user preference as a memory for future reference.
        
        Args:
            user_id: User's Firebase UID
            preference_content: The preference text
            preference_type: Type of preference
        
        Returns:
            Memory document ID
        """
        return await VectorStore.store_memory(
            user_id=user_id,
            content=preference_content,
            memory_type=preference_type,
            metadata={"source": "conversation"}
        )
    
    @classmethod
    async def update_trip_preferences(
        cls,
        trip_id: str,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> bool:
        """
        Update trip preferences after extraction from conversation.
        
        Args:
            trip_id: The trip ID
            user_id: User's Firebase UID
            preferences: Extracted preferences
        
        Returns:
            True if updated successfully
        """
        trips = trips_collection()
        
        result = await trips.update_one(
            {"_id": trip_id, "user_id": user_id},
            {
                "$set": {
                    "preferences": preferences,
                    "updated_at": datetime.now(timezone.utc)
                },
                "$setOnInsert": {
                    "_id": trip_id,
                    "user_id": user_id,
                    "created_at": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )
        
        return result.modified_count > 0 or result.upserted_id is not None
    
    @classmethod
    def format_history_for_llm(
        cls,
        history: List[Dict[str, Any]],
        max_messages: int = 10
    ) -> str:
        """
        Format conversation history as a string for LLM prompts.
        
        Args:
            history: List of message dictionaries
            max_messages: Maximum messages to include
        
        Returns:
            Formatted string of conversation history
        """
        if not history:
            return "No previous conversation."
        
        recent_history = history[-max_messages:]
        
        formatted = []
        for msg in recent_history:
            role = msg.get("role", "user").upper()
            content = msg.get("content", "")
            # Truncate long messages
            if len(content) > 500:
                content = content[:500] + "..."
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)
    
    @classmethod
    async def clear_conversation(
        cls,
        trip_id: str,
        user_id: str
    ) -> bool:
        """
        Clear conversation history for a trip.
        
        Args:
            trip_id: The trip ID
            user_id: User's Firebase UID
        
        Returns:
            True if cleared successfully
        """
        convos = conversations_collection()
        result = await convos.delete_one({"trip_id": trip_id, "user_id": user_id})
        return result.deleted_count > 0


# Singleton-like access
conversation_manager = ConversationManager()
