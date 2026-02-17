from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Destination(BaseModel):
    name: str
    description: str
    image_url: str
    category: List[str]
    rating: float = 0.0
    location: dict = Field(..., description="GeoJSON Point: {'type': 'Point', 'coordinates': [lng, lat]}")
    tags: List[str] = []
    is_trending: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DestinationResponse(BaseModel):
    results: List[Destination]
