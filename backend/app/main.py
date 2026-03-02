
"""
Watchout Backend - Main FastAPI Application
"""
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import httpx

from app.core.config import settings
from app.core.firebase_auth import init_firebase
from app.db.mongo import MongoDB
from app.api import api_router
from app.services.payment_reconciliation import (
    init_reconciliation_scheduler,
    shutdown_reconciliation_scheduler,
)


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
        shutdown_reconciliation_scheduler(app)
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

# OB5: Instrument and expose Prometheus metrics endpoint
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app, include_in_schema=False, should_gzip=True)

# OB6: Initialize OpenTelemetry for end-to-end tracing
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    # Set up tracing provider pointing to Console (or OTLP in prod)
    resource = Resource.create({SERVICE_NAME: settings.app_name or "watchout-backend"})
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)

    # Instrument MongoDB driver
    try:
        from opentelemetry.instrumentation.pymongo import PymongoInstrumentor
        PymongoInstrumentor().instrument()
    except ImportError:
        logger.warning("opentelemetry.instrumentation.pymongo missing; MongoDB not traced")
except ImportError as e:
    logger.warning("OpenTelemetry SDK not installed: %s", e)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validation error for %s: %s", request.url, exc.errors())
    return JSONResponse(
        status_code=422,
        content={"error": "validation_error", "detail": exc.errors()},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Standardised JSON envelope for all HTTP errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "http_error", "message": exc.detail},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all: prevents raw stack traces leaking to clients, but preserves CORS headers."""
    logger.error("Unhandled exception on %s: %s", request.url, exc, exc_info=True)
    
    # Attempt to extract origin from request to dynamically echo it back (if allowed)
    origin = request.headers.get("origin")
    headers = {}
    if origin in _cors_origins:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
        
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "message": "An unexpected error occurred. Please try again."},
        headers=headers
    )

# Build CORS origins dynamically
_cors_origins = [
    settings.frontend_url,
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
]
# Only allow wildcard in local development when credentials are not trusted from arbitrary origins.
if settings.app_env == "development":
    _cors_origins.append("*")
# If FRONTEND_URL looks like a domain (not localhost), also allow https variant
if settings.frontend_url and "localhost" not in settings.frontend_url:
    if not settings.frontend_url.startswith("http"):
        _cors_origins.append(f"https://{settings.frontend_url}")
# Filter out empty strings
_cors_origins = [o for o in _cors_origins if o]

# Build CORS allowed headers
_cors_headers = [
    "Authorization", 
    "Content-Type",
    "X-Timezone-Offset",
    "X-Timezone-Id",
    "X-Test-Bypass-Token"
]

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=_cors_headers,
)

from fastapi.middleware.gzip import GZipMiddleware

# Add GZip Middleware for large itinerary payload compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Request body size limit middleware (10 MB max)
@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > 10_485_760:  # 10 MB
                return JSONResponse(
                    status_code=413,
                    content={"error": "request_too_large", "message": "Request body must be under 10 MB."},
                )
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={"error": "bad_request", "message": "Invalid Content-Length header."},
            )
    return await call_next(request)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    if settings.app_env != "development":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

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
    """Health check endpoint: verifies API and backing services."""
    import asyncio
    
    health_status = {"status": "healthy", "services": {}}
    
    # 1. Check MongoDB
    try:
        if MongoDB.client:
            # Quick ping with 2s timeout
            await asyncio.wait_for(MongoDB.client.admin.command('ping'), timeout=2.0)
            health_status["services"]["mongodb"] = "connected"
        else:
            health_status["services"]["mongodb"] = "disconnected"
            health_status["status"] = "degraded"
    except Exception as e:
        logger.error(f"Healthcheck: MongoDB ping failed: {e}")
        health_status["services"]["mongodb"] = "error"
        health_status["status"] = "degraded"

    # 2. Check Redis (if configured)
    if settings.redis_url:
        try:
            import redis.asyncio as aioredis  # type: ignore
            r = aioredis.from_url(settings.redis_url)
            await asyncio.wait_for(r.ping(), timeout=2.0)
            health_status["services"]["redis"] = "connected"
            await r.close()
        except Exception as e:
            logger.error(f"Healthcheck: Redis ping failed: {e}")
            health_status["services"]["redis"] = "error"
            health_status["status"] = "degraded"

    # 3. Check Groq API
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            res = await client.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {settings.groq_api_key}"}
            )
            if res.status_code == 200:
                health_status["services"]["groq"] = "connected"
            else:
                health_status["services"]["groq"] = f"error_{res.status_code}"
                health_status["status"] = "degraded"
    except Exception as e:
        logger.error(f"Healthcheck: Groq API check failed: {e}")
        health_status["services"]["groq"] = "error"
        health_status["status"] = "degraded"

    # Return 200 even if degraded, so proxy can decide routing policy,
    # or return 503 if you prefer it to be pulled from rotation.
    status_code = 503 if health_status["status"] == "degraded" else 200
    
    return JSONResponse(status_code=status_code, content=health_status)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app_env == "development"
    )
