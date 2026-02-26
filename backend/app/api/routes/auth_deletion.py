"""
Authentication Routes - Extended with User Deletion
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timezone

from app.core.firebase_auth import verify_firebase_token
from app.models.user import UserCreate, UserUpdate, UserResponse
from app.db.mongo import users_collection
from app.services.user_deletion_service import UserDeletionService
from app.core.rate_limiter import limiter, RateLimits

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.delete("/account")
@limiter.limit(RateLimits.USER_DELETE)
async def delete_account(
    request: Request,
    token_data: dict = Depends(verify_firebase_token)
):
    """
    Delete user account and ALL associated data (DPDP Act Right to Erasure).
    
    This action is IRREVERSIBLE and will:
    - Delete user profile
    - Delete all trips
    - Delete all conversations
    - Delete all memories
    - Anonymize payment records  
    - Mark consent records as deleted
    
    Requires: Re-authentication recommended for production
    """
    user_id = token_data["uid"]
    
    # Perform cascade deletion
    stats = await UserDeletionService.delete_user_completely(user_id)
    
    # Also delete from Firebase Auth (optional - comment out if you want to keep auth)
    # from firebase_admin import auth
    # try:
    #     auth.delete_user(user_id)
    #     stats["firebase_auth"] = "deleted"
    # except Exception as e:
    #     stats["firebase_auth"] = f"error: {str(e)}"
    
    return {
        "status": "deleted",
        "message": "Account and all data permanently deleted",
        "stats": stats,
        "deleted_at": datetime.now(timezone.utc)
    }


@router.get("/deletion/verify")
async def verify_deletion(
    token_data: dict = Depends(verify_firebase_token)
):
    """
    Verify that user data has been completely deleted.
    Useful for testing and compliance audits.
    """
    user_id = token_data["uid"]
    
    checks = await UserDeletionService.verify_deletion(user_id)
    
    # All checks should be False (no data exists)
    all_clear = not any(checks.values())
    
    return {
        "user_id": user_id,
        "deletion_complete": all_clear,
        "remaining_data": checks
    }
