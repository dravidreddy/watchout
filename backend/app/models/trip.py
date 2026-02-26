"""
Watchout Backend - Trip Models
"""
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class TripStatus(str, Enum):
    PLANNING = "planning"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TransportMode(str, Enum):
    FLIGHT = "flight"
    TRAIN = "train"
    BUS = "bus"
    CAB = "cab"
    METRO = "metro"
    AUTO = "auto"
    WALKING = "walking"


class TransportLeg(BaseModel):
    """A single transportation leg between locations."""
    
    mode: TransportMode
    from_location: str
    to_location: str
    
    # Timing
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    
    # Details
    provider: Optional[str] = None  # e.g., "IndiGo", "Rajdhani Express"
    booking_link: Optional[str] = None
    estimated_cost: Optional[int] = None
    
    # For trains/flights
    number: Optional[str] = None  # e.g., "6E 123", "12301"
    class_type: Optional[str] = None  # e.g., "Economy", "3A"


class ActivityStop(BaseModel):
    """A single activity or stop in the itinerary."""
    
    name: str
    place_id: Optional[str] = None  # Google Places ID
    
    # Location
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    # Timing
    arrival_time: Optional[str] = None
    departure_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    
    # Details
    category: Optional[str] = None  # e.g., "restaurant", "attraction", "hotel"
    description: Optional[str] = None
    rating: Optional[float] = None
    price_level: Optional[int] = None
    
    # Media
    photo_url: Optional[str] = None
    
    # Booking
    booking_required: bool = False
    booking_link: Optional[str] = None
    estimated_cost: Optional[int] = None


class DayPlan(BaseModel):
    """Plan for a single day."""
    
    day_number: int
    date: Optional[date] = None
    
    # Location
    city: str
    
    # Weather
    weather: Optional[Dict[str, Any]] = None
    
    # Activities
    stops: List[ActivityStop] = Field(default_factory=list)
    
    # Transportation within the day
    transport_legs: List[TransportLeg] = Field(default_factory=list)
    
    # Notes
    notes: Optional[str] = None
    warnings: Optional[List[str]] = None  # e.g., "Heavy monsoon expected"


class AccommodationDetails(BaseModel):
    """Accommodation details for a trip."""
    
    name: str
    place_id: Optional[str] = None
    
    address: Optional[str] = None
    city: str
    
    check_in: Optional[date] = None
    check_out: Optional[date] = None
    
    type: Optional[str] = None  # hotel, hostel, resort
    rating: Optional[float] = None
    price_per_night: Optional[int] = None
    
    booking_link: Optional[str] = None
    photo_url: Optional[str] = None


class Itinerary(BaseModel):
    """Complete trip itinerary."""
    
    days: List[DayPlan] = Field(default_factory=list)
    
    # Inter-city transport
    intercity_transport: List[TransportLeg] = Field(default_factory=list)
    
    # Accommodations
    accommodations: List[AccommodationDetails] = Field(default_factory=list)
    
    # Summary
    total_estimated_cost: Optional[int] = None
    highlights: Optional[List[str]] = None


class Trip(BaseModel):
    """Complete trip document stored in MongoDB."""
    
    user_id: str
    title: str
    
    # Destinations
    cities: List[str]
    origin_city: Optional[str] = None
    
    # Dates
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    num_days: Optional[int] = None
    
    # Travelers
    num_travelers: int = 1
    
    # Budget
    budget_total: Optional[int] = None
    
    # Status
    status: TripStatus = TripStatus.PLANNING
    
    # The generated itinerary
    itinerary: Optional[Itinerary] = None
    
    # Screenshot Analysis Data
    screenshot_metadata: Optional[Dict[str, Any]] = None
    
    # Classification
    category: Optional[str] = None  # e.g., "Adventure", "Relaxation", "Family"
    tags: List[str] = Field(default_factory=list)
    
    # Visibility & Sharing
    is_public: bool = False
    sharing_id: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TripCreate(BaseModel):
    """Model for creating a new trip."""
    title: Optional[str] = None
    cities: List[str]
    origin_city: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    num_days: Optional[int] = None
    num_travelers: int = 1
    budget_total: Optional[int] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: bool = False
    itinerary: Optional[Itinerary] = None

    @model_validator(mode='after')
    def validate_dates(self):
        """EC1/EC2: Validate impossible dates and enforce chronological order."""
        start = self.start_date
        end = self.end_date
        
        if start:
            # EC1: Prevent booking trips in the past (using timezone-aware UTC current date)
            from datetime import datetime, timezone
            today = datetime.now(timezone.utc).date()
            if start < today:
                raise ValueError("start_date cannot be in the past")
                
        if start and end:
            if end < start:
                raise ValueError("end_date cannot be before start_date")
            
            # Auto-calculate num_days if not provided
            if not self.num_days:
                # EC2: Safe timedelta arithmetic
                delta = end - start
                self.num_days = delta.days + 1
                
        return self


class TripUpdate(BaseModel):
    """Model for updating a trip."""
    title: Optional[str] = None
    cities: Optional[List[str]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    num_travelers: Optional[int] = None
    budget_total: Optional[int] = None
    status: Optional[TripStatus] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None

    @model_validator(mode='after')
    def validate_dates(self):
        """EC1/EC2: Validate impossible dates if both are provided during update."""
        start = self.start_date
        end = self.end_date
        
        if start and end:
            if end < start:
                raise ValueError("end_date cannot be before start_date")
        return self


class TripResponse(BaseModel):
    """Trip response model."""
    id: str = Field(..., alias="_id")
    user_id: str
    title: str
    cities: List[str]
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    num_days: Optional[int] = None
    num_travelers: int
    status: TripStatus
    itinerary: Optional[Itinerary] = None
    category: Optional[str] = None
    tags: List[str]
    is_public: bool
    sharing_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True
