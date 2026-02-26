"""
Chat Models
"""
import re
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator


def _sanitize_input(text: str) -> str:
    """Strip HTML tags and excessive whitespace from user input."""
    text = re.sub(r"<[^>]+>", "", text)  # Remove HTML tags
    text = re.sub(r"\s+", " ", text).strip()  # Collapse whitespace
    return text


class ChatRequest(BaseModel):
    trip_id: Optional[str] = None
    message: str
    trip_context: Optional[Dict[str, Any]] = None  # profile prefs / mood from frontend

    @field_validator("message")
    @classmethod
    def sanitize_message(cls, v: str) -> str:
        v = _sanitize_input(v)
        if not v:
            raise ValueError("Message cannot be empty")
        if len(v) > 4096:
            raise ValueError("Message too long (max 4096 characters)")
        return v

class ChatResponse(BaseModel):
    response: str
    data: Optional[Dict[str, Any]] = None

