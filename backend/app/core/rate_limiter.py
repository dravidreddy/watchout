"""
Rate Limiting Configuration for Bharat Voyager API
Uses SlowAPI for per-endpoint rate limiting to prevent abuse.
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from typing import Callable
import logging

logger = logging.getLogger(__name__)


def get_user_identifier(request: Request) -> str:
    """
    Get unique identifier for rate limiting.
    Prioritizes authenticated user ID over IP address.
    """
    # Try to get user ID from Firebase token (if authenticated)
    if hasattr(request.state, "user_id"):
        return f"user:{request.state.user_id}"
    
    # Fall back to IP address for unauthenticated requests
    return f"ip:{get_remote_address(request)}"


# Initialize rate limiter
limiter = Limiter(
    key_func=get_user_identifier,
    default_limits=["200/hour", "50/minute"],  # Conservative defaults
    storage_uri="memory://",  # Use in-memory for start, switch to Redis for production
    strategy="fixed-window",
    headers_enabled=True,  # Add rate limit headers to responses
)


def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom handler for rate limit exceeded errors.
    Returns user-friendly JSON response with retry information.
    """
    logger.warning(
        f"Rate limit exceeded for {get_user_identifier(request)} "
        f"on {request.url.path}"
    )
    
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": exc.retry_after if hasattr(exc, "retry_after") else 60,
            "limit": str(exc.detail) if hasattr(exc, "detail") else "Rate limit exceeded"
        },
        headers={
            "Retry-After": str(exc.retry_after) if hasattr(exc, "retry_after") else "60"
        }
    )


def init_rate_limiter(app: FastAPI) -> None:
    """
    Initialize rate limiting for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)
    
    logger.info("Rate limiting initialized successfully")


# Predefined rate limit configurations for different endpoint types
class RateLimits:
    """Common rate limit configurations."""
    
    # Chat endpoints (most resource-intensive)
    CHAT_STREAM = "10/minute"  # SSE streaming
    CHAT_MESSAGE = "20/minute"  # Non-streaming chat
    
    # Trip management
    TRIP_CREATE = "30/hour"
    TRIP_UPDATE = "60/hour"
    TRIP_LIST = "100/hour"
    
    # User operations
    USER_UPDATE = "20/hour"
    USER_DELETE = "3/hour"  # Sensitive operation
    
    # Payment operations (sensitive)
    PAYMENT_CREATE = "10/hour"
    PAYMENT_VERIFY = "30/hour"
    
    # Public endpoints (more lenient)
    DESTINATIONS_LIST = "100/hour"
    PLACES_SEARCH = "50/hour"
    
    # Export operations (resource-intensive)
    EXPORT_PDF = "10/hour"
    
    # Auth operations
    LOGIN = "20/hour"
    SIGNUP = "10/hour"
    PASSWORD_RESET = "5/hour"  # Prevent abuse
