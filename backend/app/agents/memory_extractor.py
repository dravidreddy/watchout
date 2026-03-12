"""
Watchout Backend - Memory Extractor Agent

Runs asynchronously in the background to analyze recent conversation turns
and extract permanent long-term user preferences to store in the VectorStore.
"""
from typing import Dict, Any, List, Optional
import logging

from app.agents.base import BaseAgent
from app.services.conversation_manager import conversation_manager
from app.prompts.architecture import build_memory_extraction_prompt

logger = logging.getLogger(__name__)


class MemoryExtractorAgent(BaseAgent):
    """
    Analyzes conversation history and extracts permanent user preferences.
    Saves them directly to VectorStore via ConversationManager.
    """

    def __init__(self):
        super().__init__(
            name="Memory Extractor",
            description="Extracts actionable long-term preferences from conversation.",
            model_type="fast",  # Can use a faster, cheaper model for extraction
        )

    async def extract_and_store(
        self,
        user_id: str,
        recent_history: List[Dict[str, Any]],
        current_preferences: Dict[str, Any],
    ) -> None:
        """
        Extracts memories from the recent history and stores them.
        
        Args:
            user_id: The user's Firebase UID.
            recent_history: The recent messages to analyze.
            current_preferences: The current known preferences of the trip.
        """
        if not recent_history:
            return

        # We only really care about user messages for memory extraction
        # But seeing the assistant prompt helps context
        history_text = conversation_manager.format_history_for_llm(recent_history, max_messages=10)

        prompt = build_memory_extraction_prompt(history_text, current_preferences)

        schema = {
            "type": "object",
            "properties": {
                "extracted_memories": {
                    "type": "array",
                    "description": "List of clear, permanent user preferences. Leave empty if none found.",
                    "items": {
                        "type": "string",
                        "description": "A concise statement about the user's permanent preference (e.g., 'User is allergic to seafood', 'User hates early morning flights')."
                    }
                }
            },
            "required": ["extracted_memories"]
        }

        try:
            result = await self.generate_structured(prompt, schema)
            if not result:
                return

            memories: List[str] = result.get("extracted_memories", [])
            for memory in memories:
                if memory and isinstance(memory, str) and len(memory.strip()) > 5:
                    logger.info("Extracting new memory for user %s: %s", user_id, memory)
                    await conversation_manager.store_preference_memory(
                        user_id=user_id,
                        preference_content=memory.strip(),
                    )
        except Exception as e:
            logger.error("Failed to extract memory for user %s: %s", user_id, e)

