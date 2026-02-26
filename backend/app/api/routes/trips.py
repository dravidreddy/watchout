"""
Watchout Backend - Trip Routes
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Header
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId
import json
import logging
import uuid

from app.core.firebase_auth import verify_firebase_token
from app.core.token_limiter import check_trip_limit
from app.models.trip import TripCreate, TripUpdate, TripResponse, TripStatus
from app.db.mongo import trips_collection
from app.utils.serialization import serialize_doc, serialize_cursor

logger = logging.getLogger(__name__)

# AP3: fallback in-process idempotency store (used when Redis is not configured)
_idempotency_cache: dict = {}

# ---------------------------------------------------------------------------
# Allowlisted sort fields — prevents MongoDB injection via sort parameter
# ---------------------------------------------------------------------------
_SORT_ALLOWLIST = {"created_at", "updated_at", "title", "start_date", "end_date"}


# ---------------------------------------------------------------------------
# Itinerary body schema — prevents arbitrary dict injection into the DB
# ---------------------------------------------------------------------------
class _DayActivity(BaseModel):
    time: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    duration_minutes: Optional[int] = Field(None, ge=0, le=1440)
    category: Optional[str] = Field(None, max_length=100)
    estimated_cost: Optional[int] = Field(None, ge=0)
    tips: Optional[str] = Field(None, max_length=500)


class _ItineraryDay(BaseModel):
    day_number: int = Field(..., ge=1, le=60)
    theme: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    activities: List[_DayActivity] = Field(default_factory=list, max_length=20)
    notes: Optional[str] = Field(None, max_length=2000)


class ItineraryPayload(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    summary: Optional[str] = Field(None, max_length=2000)
    days: List[_ItineraryDay] = Field(..., max_length=60)
    total_estimated_budget: Optional[int] = Field(None, ge=0)
    highlights: Optional[List[str]] = Field(default_factory=list)

router = APIRouter(prefix="/trips", tags=["Trips"])


async def _find_user_trip(trips, trip_id: str, user_id: str):
    """
    Find a trip by trying both ObjectId (_id) and UUID (trip_id) lookups.
    This bridges the two ID strategies used by trips.py and chat.py.
    """
    # Try ObjectId lookup first (trips created via CRUD endpoints)
    try:
        trip = await trips.find_one({"_id": ObjectId(trip_id), "user_id": user_id})
        if trip:
            return trip
    except Exception:
        pass
    
    # Fall back to trip_id lookup (trips created via chat)
    trip = await trips.find_one({"trip_id": trip_id, "user_id": user_id})
    return trip


@router.post("/", response_model=dict)
async def create_trip(
    trip_data: TripCreate,
    token_data: dict = Depends(verify_firebase_token),
    x_idempotency_key: Optional[str] = Header(default=None),  # AP3
):
    """Create a new trip.

    If the client provides an X-Idempotency-Key header, subsequent identical
    requests within 24 hours return the cached result without creating a
    duplicate (AP3 — prevents double-submission on network retries).
    """
    user_id = token_data["uid"]
    
    # Enforce trip limit for free users
    await check_trip_limit(user_id)
    
    trips = trips_collection()

    # AP3: Check idempotency cache
    if x_idempotency_key:
        idem_cache_key = f"idem:create_trip:{user_id}:{x_idempotency_key}"
        cached_result = None

        # Try Redis first
        try:
            from app.core.config import settings
            import redis.asyncio as aioredis  # type: ignore
            if settings.redis_url:
                r = aioredis.from_url(settings.redis_url, decode_responses=True)
                stored = await r.get(idem_cache_key)
                if stored:
                    logger.info("Idempotency cache hit (Redis): %s", idem_cache_key)
                    return json.loads(stored)
        except Exception:
            pass  # Redis unavailable — fall through to in-process cache

        # In-process fallback
        if idem_cache_key in _idempotency_cache:
            logger.info("Idempotency cache hit (memory): %s", idem_cache_key)
            return _idempotency_cache[idem_cache_key]

    # Generate title if not provided
    title = trip_data.title
    if not title:
        cities = ", ".join(trip_data.cities[:2])
        title = f"Trip to {cities}"

    trip_doc = {
        "user_id": user_id,
        "title": title,
        "cities": trip_data.cities,
        "origin_city": trip_data.origin_city,
        "start_date": trip_data.start_date.isoformat() if trip_data.start_date else None,
        "end_date": trip_data.end_date.isoformat() if trip_data.end_date else None,
        "num_days": trip_data.num_days,
        "num_travelers": trip_data.num_travelers,
        "budget_total": trip_data.budget_total,
        "status": TripStatus.PLANNING.value,
        "itinerary": trip_data.itinerary.dict() if trip_data.itinerary else None,
        "category": trip_data.category,
        "tags": trip_data.tags or [],
        "is_public": trip_data.is_public,
        "sharing_id": uuid.uuid4().hex if trip_data.is_public else None,
        "trip_id": uuid.uuid4().hex,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    await trips.insert_one(trip_doc)
    result = {"trip_id": trip_doc["trip_id"], "status": "created"}

    # AP3: Store result in idempotency cache
    if x_idempotency_key:
        try:
            from app.core.config import settings
            import redis.asyncio as aioredis  # type: ignore
            if settings.redis_url:
                r = aioredis.from_url(settings.redis_url, decode_responses=True)
                await r.setex(idem_cache_key, 86400, json.dumps(result))
        except Exception:
            pass
        _idempotency_cache[idem_cache_key] = result  # in-process fallback always set

    return result



@router.get("/explore", response_model=List[dict])
async def explore_trips(
    city: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),  # cap: never return >100 public trips
):
    """Get public trips for exploration with optional filters."""
    trips = trips_collection()

    query = {"is_public": True, "is_trip": True}  # only show fully-saved trips
    if city:
        query["cities"] = city
    if category:
        query["category"] = category
    if tag:
        query["tags"] = tag

    cursor = trips.find(query).sort("created_at", -1).limit(limit)

    return await serialize_cursor(cursor)


@router.get("/shared/{sharing_id}", response_model=dict)
async def get_shared_trip(sharing_id: str):
    """Get a public trip by its sharing ID (no auth required)."""
    trips = trips_collection()
    
    trip = await trips.find_one({"sharing_id": sharing_id, "is_public": True})
    
    if not trip:
        raise HTTPException(status_code=404, detail="Shared trip not found")
        
    return serialize_doc(trip)


@router.get("/", response_model=List[dict])
async def list_trips(
    status: Optional[str] = None,
    city: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: int = -1,
    token_data: dict = Depends(verify_firebase_token)
):
    """List all trips for the current user with optional filters."""
    user_id = token_data["uid"]
    trips = trips_collection()

    # Allowlist sort params to prevent MongoDB operator injection
    if sort_by not in _SORT_ALLOWLIST:
        sort_by = "created_at"
    if sort_order not in (1, -1):
        sort_order = -1

    query = {"user_id": user_id, "is_trip": True}
    if status:
        query["status"] = status
    if city:
        query["cities"] = city

    if start_date or end_date:
        date_query = {}
        if start_date:
            date_query["$gte"] = start_date
        if end_date:
            date_query["$lte"] = end_date
        query["start_date"] = date_query

    cursor = trips.find(query).sort(sort_by, sort_order).limit(50)
    return await serialize_cursor(cursor)



@router.get("/search", response_model=List[dict])
async def search_trips(
    q: str,
    token_data: dict = Depends(verify_firebase_token)
):
    """Search trips by title or cities using text index."""
    user_id = token_data["uid"]
    trips = trips_collection()
    
    query = {
        "user_id": user_id,
        "$text": {"$search": q}
    }
    
    # Sort by text score
    cursor = trips.find(
        query,
        {"score": {"$meta": "textScore"}}
    ).sort([("score", {"$meta": "textScore"})]).limit(20)
    return await serialize_cursor(cursor)


@router.get("/{trip_id}", response_model=dict)
async def get_trip(
    trip_id: str,
    token_data: dict = Depends(verify_firebase_token)
):
    """Get a specific trip by ID (supports both ObjectId and UUID trip_id)."""
    user_id = token_data["uid"]
    trips = trips_collection()
    
    trip = await _find_user_trip(trips, trip_id, user_id)
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    return serialize_doc(trip)


@router.put("/{trip_id}", response_model=dict)
async def update_trip(
    trip_id: str,
    update_data: TripUpdate,
    token_data: dict = Depends(verify_firebase_token)
):
    """Update a trip."""
    user_id = token_data["uid"]
    trips = trips_collection()
    
    update_doc = {"updated_at": datetime.now(timezone.utc)}
    
    if update_data.title is not None:
        update_doc["title"] = update_data.title
    if update_data.cities is not None:
        update_doc["cities"] = update_data.cities
    if update_data.start_date is not None:
        update_doc["start_date"] = update_data.start_date.isoformat()
    if update_data.end_date is not None:
        update_doc["end_date"] = update_data.end_date.isoformat()
    if update_data.num_travelers is not None:
        update_doc["num_travelers"] = update_data.num_travelers
    if update_data.budget_total is not None:
        update_doc["budget_total"] = update_data.budget_total
    if update_data.status is not None:
        update_doc["status"] = update_data.status.value
    if update_data.category is not None:
        update_doc["category"] = update_data.category
    if update_data.tags is not None:
        update_doc["tags"] = update_data.tags
    new_sharing_id = None
    if update_data.is_public is not None:
        update_doc["is_public"] = update_data.is_public
        if update_data.is_public:
            # Generate sharing_id if it doesn't exist
            current_trip = await _find_user_trip(trips, trip_id, user_id)
            if current_trip:
                if not current_trip.get("sharing_id"):
                    new_sharing_id = uuid.uuid4().hex
                    update_doc["sharing_id"] = new_sharing_id
                else:
                    new_sharing_id = current_trip.get("sharing_id")
    
    # Find the trip first, then update using its actual _id
    trip = await _find_user_trip(trips, trip_id, user_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    await trips.update_one(
        {"_id": trip["_id"]},
        {"$set": update_doc}
    )
    
    return {"status": "updated", "sharing_id": new_sharing_id}


@router.delete("/{trip_id}", response_model=dict)
async def delete_trip(
    trip_id: str,
    token_data: dict = Depends(verify_firebase_token)
):
    """Delete a trip (supports both ObjectId and UUID trip_id)."""
    user_id = token_data["uid"]
    trips = trips_collection()
    
    trip = await _find_user_trip(trips, trip_id, user_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    await trips.delete_one({"_id": trip["_id"]})
    return {"status": "deleted"}


@router.post("/{trip_id}/itinerary", response_model=dict)
async def save_itinerary(
    trip_id: str,
    itinerary: ItineraryPayload,  # validated schema — no arbitrary dict injection
    token_data: dict = Depends(verify_firebase_token)
):
    """Save an itinerary to a trip (supports both ObjectId and UUID trip_id)."""
    user_id = token_data["uid"]
    trips = trips_collection()

    trip = await _find_user_trip(trips, trip_id, user_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    await trips.update_one(
        {"_id": trip["_id"]},
        {
            "$set": {
                "itinerary": itinerary.model_dump(),
                "status": TripStatus.PLANNING.value,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    return {"status": "saved"}

@router.get("/shared/{sharing_id}", response_model=TripResponse)
async def get_shared_trip(sharing_id: str):
    """Get a public trip by its sharing ID (NO auth required)."""
    trips = trips_collection()
    trip = await trips.find_one({"sharing_id": sharing_id, "is_public": True})
    if not trip:
        raise HTTPException(status_code=404, detail="Shared trip not found or is private")
    
    return serialize_doc(trip)
