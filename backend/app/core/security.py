"""
Watchout Backend - Security Utilities
"""
import hmac
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import jwt
from app.core.config import settings


def generate_secret_key(length: int = 32) -> str:
    """Generate a cryptographically secure secret key."""
    return secrets.token_urlsafe(length)


def verify_razorpay_signature(
    order_id: str,
    payment_id: str,
    signature: str
) -> bool:
    """
    Verify Razorpay payment signature.
    Uses HMAC-SHA256 as per Razorpay documentation.
    """
    message = f"{order_id}|{payment_id}"
    
    expected_signature = hmac.new(
        key=settings.razorpay_key_secret.encode(),
        msg=message.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)


def verify_razorpay_webhook_signature(
    payload: bytes,
    signature: str
) -> bool:
    """
    Verify Razorpay webhook signature.
    """
    expected_signature = hmac.new(
        key=settings.razorpay_webhook_secret.encode(),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)


def create_internal_token(
    user_id: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create an internal JWT token for inter-service communication.
    Not used for user authentication (Firebase handles that).
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=24)
    
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    
    return jwt.encode(
        payload,
        settings.app_secret_key,
        algorithm="HS256"
    )


def verify_internal_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify an internal JWT token.
    """
    try:
        payload = jwt.decode(
            token,
            settings.app_secret_key,
            algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for storage.
    Uses SHA-256 for one-way hashing.
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """
    Sanitize user input to prevent injection attacks.
    Removes control characters and limits length.
    """
    if not text:
        return ""
    
    # Remove control characters except newlines and tabs
    sanitized = "".join(
        char for char in text
        if char.isprintable() or char in "\n\t"
    )
    
    # Limit length
    return sanitized[:max_length]
