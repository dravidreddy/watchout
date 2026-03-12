from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from bson import ObjectId
import logging
import re

from app.core.firebase_auth import verify_firebase_token
from app.db.mongo import trips_collection
from app.services.pdf_generator import itinerary_pdf_service

router = APIRouter(prefix="/export", tags=["Export"])
logger = logging.getLogger(__name__)

@router.get("/pdf/{trip_id}")
async def export_itinerary_to_pdf(
    trip_id: str,
    token_data: dict = Depends(verify_firebase_token)
):
    """Generate and return a PDF for a trip itinerary."""
    user_id = token_data["uid"]
    trips = trips_collection()

    query_conditions = [{"trip_id": trip_id}]
    try:
        query_conditions.append({"_id": ObjectId(trip_id)})
    except Exception:
        pass

    trip = await trips.find_one({
        "$or": query_conditions,
        "user_id": user_id,
    })
        
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    if not trip.get("itinerary"):
        raise HTTPException(status_code=400, detail="Itinerary not found for this trip")
        
    try:
        pdf_bytes = await itinerary_pdf_service.generate_itinerary_pdf(trip)
        safe_title = re.sub(r"[^A-Za-z0-9._-]+", "_", str(trip.get("title", "trip"))).strip("._")
        if not safe_title:
            safe_title = "trip"
        filename = f"Itinerary_{safe_title}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        error_msg = str(e)
        logger.error("Failed to generate itinerary PDF for trip_id=%s user_id=%s: %s", trip_id, user_id, error_msg, exc_info=True)
        if "Executable doesn't exist" in error_msg or "Chromium" in error_msg:
            raise HTTPException(
                status_code=500, 
                detail="PDF export is temporarily unavailable because the browser runtime is missing on the server."
            )
        raise HTTPException(status_code=500, detail="Failed to generate PDF")
