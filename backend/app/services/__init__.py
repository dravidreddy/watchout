"""
Watchout Backend - Services Package
"""
from app.services.conversation_manager import ConversationManager, conversation_manager

__all__ = [
    "ConversationManager",
    "conversation_manager"
]
