"""
Watchout Backend - Core Module
"""
from app.core.config import settings, get_settings
from app.core.firebase_auth import (
    init_firebase,
    verify_firebase_token,
    get_current_user,
    get_optional_user
)
from app.core.security import (
    verify_razorpay_signature,
    verify_razorpay_webhook_signature,
    sanitize_input
)

__all__ = [
    "settings",
    "get_settings",
    "init_firebase",
    "verify_firebase_token",
    "get_current_user",
    "get_optional_user",
    "verify_razorpay_signature",
    "verify_razorpay_webhook_signature",
    "sanitize_input"
]
