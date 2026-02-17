
"""
Watchout Backend - Main FastAPI Application
"""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.firebase_auth import init_firebase
from app.db.mongo import MongoDB
from app.api import api_router
from app.services.payment_reconciliation import init_reconciliation_scheduler


# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    try:
        # Validate required environment variables FIRST
        logger.info("[STARTUP] Validating environment variables...")
        validate_environment()
        logger.info("[SUCCESS] Environment validation passed")
        
        # Startup
        logger.info("[STARTUP] Starting Watchout Backend...")

        # Initialize database connection
        await MongoDB.connect()
        logger.info("[SUCCESS] Database connection established")
        
        # Initialize Firebase Admin
        init_firebase()
        logger.info("[SUCCESS] Firebase initialized")
        
        # Initialize rate limiter
        from app.core.rate_limiter import init_rate_limiter
        init_rate_limiter(app)
        logger.info("[SUCCESS] Rate limiting enabled")
        
        # Initialize payment reconciliation scheduler
        init_reconciliation_scheduler(app)
        logger.info("[SUCCESS] Payment reconciliation scheduler initialized")
        
        yield
        
    except Exception as e:
        logger.error(f"[ERROR] Startup error: {e}")
        raise
    finally:
        # Cleanup on shutdown
        logger.info("[SHUTDOWN] Shutting down...")
        await MongoDB.disconnect()
        logger.info("[SUCCESS] Database connection closed")


def validate_environment():
    """
    Validate that all required environment variables are set.
    Raises RuntimeError if any critical variables are missing.
    """
    # Critical variables required for production
    critical_vars = {
        "MONGODB_URI": settings.mongodb_uri,
        "GROQ_API_KEY": settings.groq_api_key,
    }
    
    # Warning-level variables (app can run without, but degraded)
    warning_vars = {
        "GOOGLE_PLACES_API_KEY": settings.google_places_api_key,
        "WEATHERAPI_KEY": settings.weatherapi_key,
        "FIREBASE_PROJECT_ID": settings.firebase_project_id,
        "RAZORPAY_KEY_ID": settings.razorpay_key_id,
        "RAZORPAY_KEY_SECRET": settings.razorpay_key_secret,
    }
    
    missing_critical = [name for name, val in critical_vars.items() if not val or val == ""]
    missing_warnings = [name for name, val in warning_vars.items() if not val or val == ""]
    
    if missing_critical:
        raise RuntimeError(
            f"[CRITICAL] Missing required environment variables: {', '.join(missing_critical)}\n"
            f"Please set these in your .env file before starting the application."
        )
    
    if missing_warnings:
        logger.warning(
            f"[WARNING] Optional environment variables not set: {', '.join(missing_warnings)}\n"
            f"Some features may be degraded."
        )


app = FastAPI(
    title=settings.app_name,
    description="AI-powered travel itinerary planner for India",
    version="1.0.0",
    lifespan=lifespan
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"DEBUG: Validation error for {request.url}")
    print(f"DEBUG: Errors: {exc.errors()}")
    print(f"DEBUG: Body: {await request.body()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(await request.body())},
    )

# Build CORS origins dynamically
_cors_origins = [
    settings.frontend_url,
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
]
# If FRONTEND_URL looks like a domain (not localhost), also allow https variant
if settings.frontend_url and "localhost" not in settings.frontend_url:
    if not settings.frontend_url.startswith("http"):
        _cors_origins.append(f"https://{settings.frontend_url}")
# Filter out empty strings
_cors_origins = [o for o in _cors_origins if o]

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected" if MongoDB.client else "disconnected"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development"
    )
