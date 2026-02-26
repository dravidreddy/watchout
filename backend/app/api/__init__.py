"""
Watchout Backend - API Router
"""
from fastapi import APIRouter

# Import all route modules
from app.api.routes import (
    chat,
    trips,
    auth,
    payments,
    export,
    consent,  # DPDP Act compliance routes
    webhooks,  # Payment webhooks
    destinations,  # Destinations and trending places
    places,  # Google Places search
    tools  # External tool endpoints (Reel Extraction)
)

api_router = APIRouter()

# Include all route modules
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(trips.router)
api_router.include_router(auth.router)
api_router.include_router(payments.router)
api_router.include_router(export.router)
api_router.include_router(consent.router)  # DPDP Act compliance
api_router.include_router(webhooks.router)  # Payment webhooks
api_router.include_router(destinations.router)  # Destinations
api_router.include_router(places.router)  # Places search
api_router.include_router(tools.router)  # Tools

