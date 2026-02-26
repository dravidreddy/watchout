"""
Watchout Backend - User Models
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TravelStyle(str, Enum):
    RELAXING = "relaxing"
    ADVENTURE = "adventure"
    CULTURAL = "cultural"
    BALANCED = "balanced"
    # Keeping old ones for compatibility
    SOLO = "solo"
    COUPLE = "couple"
    FRIENDS = "friends"
    FAMILY = "family"


class TravelVibe(str, Enum):
    ADVENTURE = "adventure"
    CHILL = "chill"
    CULTURAL = "cultural"
    PARTY = "party"
    ROMANTIC = "romantic"


class PacePreference(str, Enum):
    RELAXED = "relaxed"
    MODERATE = "moderate"
    PACKED = "packed"


class BudgetRange(str, Enum):
    BUDGET = "budget"
    MID_RANGE = "mid-range"  # Changed to match frontend hyphen
    LUXURY = "luxury"


class UserPreferences(BaseModel):
    """User travel preferences."""
    
    # Destination preferences
    beach_vs_mountain: Optional[str] = Field(
        default=None,
        description="Preference: beach, mountain, or both"
    )
    
    # Language
    language: Optional[str] = Field(
        default="English",
        description="Preferred language for AI responses"
    )
    
    # Travel style
    travel_style: Optional[TravelStyle] = None
    travel_vibe: Optional[List[TravelVibe]] = Field(default_factory=list)
    
    # Budget
    budget_range: Optional[BudgetRange] = None
    daily_budget_inr: Optional[int] = Field(
        default=None,
        description="Daily budget in INR"
    )
    
    # Food preferences
    food_preferences: Optional[List[str]] = Field(
        default_factory=list,
        description="e.g., vegetarian, vegan, local, international"
    )
    cuisine_preferences: Optional[List[str]] = Field(
        default_factory=list,
        description="e.g., North Indian, South Indian, Chinese"
    )
    
    # Pace
    pace_preference: Optional[PacePreference] = None
    
    # Transportation
    preferred_transport: Optional[List[str]] = Field(
        default_factory=list,
        description="e.g., flight, train, bus, car"
    )
    
    # Accommodation
    accommodation_type: Optional[List[str]] = Field(
        default_factory=list,
        description="e.g., hotel, hostel, homestay, resort"
    )
    
    # Special interests
    interests: Optional[List[str]] = Field(
        default_factory=list,
        description="e.g., photography, trekking, food tours, history"
    )


class UserProfile(BaseModel):
    """User profile stored in MongoDB."""
    
    firebase_id: str = Field(..., description="Firebase UID")
    email: EmailStr
    name: Optional[str] = None
    photo_url: Optional[str] = None
    phone: Optional[str] = None
    
    # Location
    home_city: Optional[str] = None
    
    # Preferences
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    
    # Onboarding
    onboarding_completed: bool = False
    
    # Subscription
    subscription_tier: str = Field(default="free")
    subscription_expiry: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None


class UserCreate(BaseModel):
    """Model for creating a new user."""
    firebase_id: str
    email: EmailStr
    name: Optional[str] = None
    photo_url: Optional[str] = None


class UserUpdate(BaseModel):
    """Model for updating user profile."""
    name: Optional[str] = None
    phone: Optional[str] = None
    home_city: Optional[str] = None
    preferences: Optional[UserPreferences] = None
    onboarding_completed: Optional[bool] = None
    subscription_tier: Optional[str] = None


class UserResponse(BaseModel):
    """User response model (excludes sensitive data)."""
    id: str = Field(..., alias="_id")
    firebase_id: str
    email: EmailStr
    name: Optional[str] = None
    photo_url: Optional[str] = None
    home_city: Optional[str] = None
    preferences: UserPreferences
    onboarding_completed: bool
    subscription_tier: str
    created_at: datetime
    
    class Config:
        populate_by_name = True
