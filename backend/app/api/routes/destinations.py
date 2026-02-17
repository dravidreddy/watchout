from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from bson import ObjectId

from app.core.firebase_auth import verify_firebase_token
from app.db.mongo import MongoDB
from app.services import recommendations

router = APIRouter(prefix="/destinations", tags=["Destinations"])

def destinations_collection():
    return MongoDB.get_collection("destinations")

@router.get("/trending", response_model=List[dict])
async def get_trending_destinations():
    """Get trending destinations."""
    collection = destinations_collection()
    cursor = collection.find({"is_trending": True}).limit(10)
    result = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        result.append(doc)
    
    # If no data, return some default placeholders to avoid empty UI
    if not result:
        return []
        
    return result

@router.get("/nearby", response_model=List[dict])
async def get_nearby_destinations(
    lat: float,
    lng: float,
    radius_km: float = 1000
):
    """Get destinations near a location."""
    collection = destinations_collection()
    
    query = {
        "location": {
            "$near": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": [lng, lat]
                },
                "$maxDistance": radius_km * 1000
            }
        }
    }
    
    cursor = collection.find(query).limit(10)
    result = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        result.append(doc)
    return result

@router.get("/suggestions", response_model=List[str])
async def get_user_suggestions(
    token_data: dict = Depends(verify_firebase_token)
):
    """Get personalized AI suggestions for the user."""
    user_id = token_data["uid"]
    return await recommendations.get_personalized_suggestions(user_id)
