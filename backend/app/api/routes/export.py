from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from bson import ObjectId

from app.core.firebase_auth import verify_firebase_token
from app.db.mongo import trips_collection
from app.services.pdf_generator import itinerary_pdf_service

router = APIRouter(prefix="/export", tags=["Export"])

@router.get("/pdf/{trip_id}")
async def export_itinerary_to_pdf(
    trip_id: str,
    token_data: dict = Depends(verify_firebase_token)
):
    """Generate and return a PDF for a trip itinerary."""
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
        
    if not trip.get("itinerary"):
        raise HTTPException(status_code=400, detail="Itinerary not found for this trip")
        
    try:
        pdf_bytes = await itinerary_pdf_service.generate_itinerary_pdf(trip)
        
        filename = f"Itinerary_{trip['title'].replace(' ', '_')}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
