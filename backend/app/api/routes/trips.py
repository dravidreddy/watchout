"""
Watchout Backend - Trip Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import uuid

from app.core.firebase_auth import verify_firebase_token
from app.models.trip import TripCreate, TripUpdate, TripResponse, TripStatus
from app.db.mongo import trips_collection

router = APIRouter(prefix="/trips", tags=["Trips"])


@router.post("/", response_model=dict)
async def create_trip(
    trip_data: TripCreate,
    token_data: dict = Depends(verify_firebase_token)
):
    """Create a new trip."""
    user_id = token_data["uid"]
    trips = trips_collection()
    
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
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await trips.insert_one(trip_doc)
    return {"trip_id": str(result.inserted_id), "status": "created"}


@router.get("/explore", response_model=List[dict])
async def explore_trips(
    city: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 20
):
    """Get public trips for exploration with optional filters."""
    trips = trips_collection()
    
    query = {"is_public": True}
    if city:
        query["cities"] = city
    if category:
        query["category"] = category
    if tag:
        query["tags"] = tag
        
    cursor = trips.find(query).sort("created_at", -1).limit(limit)
    
    result = []
    async for trip in cursor:
        trip["_id"] = str(trip["_id"])
        result.append(trip)
    
    return result


@router.get("/shared/{sharing_id}", response_model=dict)
async def get_shared_trip(sharing_id: str):
    """Get a public trip by its sharing ID (no auth required)."""
    trips = trips_collection()
    
    trip = await trips.find_one({"sharing_id": sharing_id, "is_public": True})
    
    if not trip:
        raise HTTPException(status_code=404, detail="Shared trip not found")
        
    trip["_id"] = str(trip["_id"])
    return trip


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
    
    query = {"user_id": user_id}
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
    
    result = []
    async for trip in cursor:
        trip["_id"] = str(trip["_id"])
        result.append(trip)
    
    return result


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
    
    result = []
    async for trip in cursor:
        trip["_id"] = str(trip["_id"])
        result.append(trip)
    
    return result


@router.get("/{trip_id}", response_model=dict)
async def get_trip(
    trip_id: str,
    token_data: dict = Depends(verify_firebase_token)
):
    """Get a specific trip by ID."""
    user_id = token_data["uid"]
    trips = trips_collection()
    
    try:
        trip = await trips.find_one({
            "_id": ObjectId(trip_id),
            "user_id": user_id
        })
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid trip ID")
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    trip["_id"] = str(trip["_id"])
    return trip


@router.put("/{trip_id}", response_model=dict)
async def update_trip(
    trip_id: str,
    update_data: TripUpdate,
    token_data: dict = Depends(verify_firebase_token)
):
    """Update a trip."""
    user_id = token_data["uid"]
    trips = trips_collection()
    
    update_doc = {"updated_at": datetime.utcnow()}
    
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
    if update_data.is_public is not None:
        update_doc["is_public"] = update_data.is_public
        if update_data.is_public:
            # Generate sharing_id if it doesn't exist
            current_trip = await trips.find_one({"_id": ObjectId(trip_id)})
            if current_trip and not current_trip.get("sharing_id"):
                update_doc["sharing_id"] = uuid.uuid4().hex
    
    
    try:
        result = await trips.update_one(
            {"_id": ObjectId(trip_id), "user_id": user_id},
            {"$set": update_doc}
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid trip ID")
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    return {"status": "updated"}


@router.delete("/{trip_id}", response_model=dict)
async def delete_trip(
    trip_id: str,
    token_data: dict = Depends(verify_firebase_token)
):
    """Delete a trip."""
    user_id = token_data["uid"]
    trips = trips_collection()
    
    # Try to delete using both ObjectId and string _id formats
    # Some trips use ObjectId, others use string IDs like "trip_xxx"
    try:
        # First try as ObjectId
        result = await trips.delete_one({
            "_id": ObjectId(trip_id),
            "user_id": user_id
        })
    except Exception:
        # If ObjectId conversion fails, try as string
        result = await trips.delete_one({
            "_id": trip_id,
            "user_id": user_id
        })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    return {"status": "deleted"}


@router.post("/{trip_id}/itinerary", response_model=dict)
async def save_itinerary(
    trip_id: str,
    itinerary: dict,
    token_data: dict = Depends(verify_firebase_token)
):
    """Save an itinerary to a trip."""
    user_id = token_data["uid"]
    trips = trips_collection()
    
    try:
        result = await trips.update_one(
            {"_id": ObjectId(trip_id), "user_id": user_id},
            {
                "$set": {
                    "itinerary": itinerary,
                    "status": TripStatus.PLANNING.value,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid trip ID")
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    return {"status": "saved"}
