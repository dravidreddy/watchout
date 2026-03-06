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
        
        filename = f"Itinerary_{trip['title'].replace(' ', '_')}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        error_msg = str(e)
        if "Executable doesn't exist" in error_msg or "Chromium" in error_msg:
            raise HTTPException(
                status_code=500, 
                detail=f"PDF Generator Error (Missing Chromium dependency): {error_msg}. Try running 'playwright install chromium' on the server."
            )
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {error_msg}")
