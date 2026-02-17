"""
Watchout Backend - Firebase Authentication
"""
import firebase_admin
from firebase_admin import auth, credentials
from fastapi import HTTPException, Security, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any

from app.core.config import settings


# Initialize Firebase Admin SDK
_firebase_app: Optional[firebase_admin.App] = None


def init_firebase() -> None:
    """Initialize Firebase Admin SDK with service account credentials."""
    global _firebase_app
    
    if _firebase_app is not None:
        return
    
    try:
        # Build credentials from environment variables
        cred_dict = {
            "type": "service_account",
            "project_id": settings.firebase_project_id,
            "private_key": settings.firebase_private_key.replace("\\n", "\n"),
            "client_email": settings.firebase_client_email,
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        
        cred = credentials.Certificate(cred_dict)
        _firebase_app = firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK initialized successfully")
    except Exception as e:
        print(f"Warning: Firebase initialization failed: {e}")
        print("Authentication will not work until Firebase is properly configured")


# Security scheme for Bearer token
security = HTTPBearer(auto_error=False)


async def verify_firebase_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    x_test_bypass_token: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Verify Firebase ID token from Authorization header.
    Returns decoded token with user info.
    Supports Dev Bypass with X-Test-Bypass-Token header.
    """
    # 1. Check for Dev Bypass
    if settings.app_env == "development" and x_test_bypass_token:
        if x_test_bypass_token == settings.dev_bypass_secret:
            return {
                "uid": "test-user-123",
                "email": "qa@watchout.app",
                "name": "QA Tester",
                "picture": "",
                "email_verified": True,
                "is_dev_bypass": True
            }
    
    # 2. Standard Firebase Verification
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization header"
        )
    
    token = credentials.credentials
    
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )


async def get_current_user(
    token_data: Dict[str, Any] = Depends(verify_firebase_token)
) -> Dict[str, Any]:
    """
    Get current authenticated user from token.
    Returns user info including uid, email, name, and picture.
    """
    return {
        "uid": token_data.get("uid"),
        "email": token_data.get("email"),
        "name": token_data.get("name"),
        "picture": token_data.get("picture"),
        "email_verified": token_data.get("email_verified", False)
    }


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    x_test_bypass_token: Optional[str] = Header(None)
) -> Optional[Dict[str, Any]]:
    """
    Optionally get current user - returns None if not authenticated.
    Useful for routes that work with or without authentication.
    """
    # 1. Check for Dev Bypass
    if settings.app_env == "development" and x_test_bypass_token:
        if x_test_bypass_token == settings.dev_bypass_secret:
            return {
                "uid": "test-user-123",
                "email": "qa@watchout.app",
                "name": "QA Tester",
                "picture": "",
                "email_verified": True
            }

    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        decoded_token = auth.verify_id_token(token)
        return {
            "uid": decoded_token.get("uid"),
            "email": decoded_token.get("email"),
            "name": decoded_token.get("name"),
            "picture": decoded_token.get("picture")
        }
    except Exception:
        return None
