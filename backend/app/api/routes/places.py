"""
Watchout Backend - Places Routes (Google Places Proxy)
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List

from app.core.firebase_auth import verify_firebase_token
from app.tools.google_places import get_places_tool

router = APIRouter(prefix="/places", tags=["Places"])


@router.get("/search")
async def search_places(
    query: str,
    location: Optional[str] = None,
    place_type: Optional[str] = None,
    token_data: dict = Depends(verify_firebase_token)
):
    """Search for places using Google Places API."""
    places = get_places_tool()
    results = await places.search_places(query, location, place_type=place_type)
    return {"results": results}


@router.get("/nearby")
async def search_nearby(
    latitude: float,
    longitude: float,
    radius: int = 1500,
    place_type: str = "tourist_attraction",
    keyword: Optional[str] = None,
    token_data: dict = Depends(verify_firebase_token)
):
    """Search for nearby places."""
    places = get_places_tool()
    results = await places.search_nearby(latitude, longitude, radius, place_type, keyword)
    return {"results": results}


@router.get("/details/{place_id}")
async def get_place_details(
    place_id: str,
    token_data: dict = Depends(verify_firebase_token)
):
    """Get detailed information about a place."""
    places = get_places_tool()
    details = await places.get_place_details(place_id)
    
    if not details:
        raise HTTPException(status_code=404, detail="Place not found")
    
    return details


@router.get("/autocomplete")
async def place_autocomplete(
    input: str,
    types: Optional[str] = None,
    token_data: dict = Depends(verify_firebase_token)
):
    """Get place autocomplete suggestions."""
    places = get_places_tool()
    predictions = await places.autocomplete(input, types)
    return {"predictions": predictions}


@router.get("/photo/{photo_reference}")
async def get_place_photo(
    photo_reference: str,
    max_width: int = 400
):
    """
    Proxy endpoint for Google Places photos.
    This is PUBLIC (no auth required) because:
    - Browser <img> tags cannot send Authorization headers
    - photo_reference is a temporary token from Google, safe to expose
    - API key remains secure on backend
    """
    from fastapi.responses import RedirectResponse
    
    places = get_places_tool()
    photo_url = places.get_photo_url(photo_reference, max_width)
    
    # Redirect to the actual Google Places photo URL
    return RedirectResponse(url=photo_url)
