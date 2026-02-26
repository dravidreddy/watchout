"""
Authentication Routes
Includes login, profile management, and account deletion (DPDP Act compliance).
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timezone

from app.core.firebase_auth import verify_firebase_token
from app.models.user import UserCreate, UserUpdate, UserResponse, UserPreferences
from app.db.mongo import users_collection  
from app.services.user_deletion_service import UserDeletionService
from app.core.rate_limiter import limiter, RateLimits

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=UserResponse)
async def login_user(
    user_data: UserCreate,
    token_data: dict = Depends(verify_firebase_token)
):
    """Login or Register a user from Firebase auth."""
    # Validate that the token's uid matches the provided firebase_id
    if token_data["uid"] != user_data.firebase_id:
        raise HTTPException(
            status_code=403,
            detail="Token UID does not match provided firebase_id"
        )
    users = users_collection()
    
    # Check if user exists
    existing = await users.find_one({"firebase_id": user_data.firebase_id})
    if existing:
        existing["_id"] = str(existing["_id"])
        return existing
    
    # Create user document
    user_doc = {
        "firebase_id": user_data.firebase_id,
        "email": user_data.email,
        "name": user_data.name,
        "photo_url": user_data.photo_url,
        "preferences": {},
        "onboarding_completed": False,
        "subscription_tier": "free",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    
    result = await users.insert_one(user_doc)
    user_doc["_id"] = str(result.inserted_id)
    return user_doc


@router.get("/me", response_model=dict)
async def get_current_user_profile(
    token_data: dict = Depends(verify_firebase_token)
):
    """Get current user's profile."""
    users = users_collection()
    user = await users.find_one({"firebase_id": token_data["uid"]})
    
    # Auto-create user for Dev Bypass if missing
    if not user and token_data.get("is_dev_bypass"):
        user_doc = {
            "firebase_id": token_data["uid"],
            "email": token_data["email"],
            "name": token_data["name"],
            "photo_url": token_data.get("picture", ""),
            "preferences": {},
            "onboarding_completed": False,
            "subscription_tier": "free",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        result = await users.insert_one(user_doc)
        user_doc["_id"] = str(result.inserted_id)
        return user_doc

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user["_id"] = str(user["_id"])
    # Pass along bypass status if present in token for test transparency
    if token_data.get("is_dev_bypass"):
        user["is_dev_bypass"] = True
        
    return user


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    update_data: UserUpdate,
    token_data: dict = Depends(verify_firebase_token)
):
    """Update current user's profile."""
    users = users_collection()
    
    update_doc = {"updated_at": datetime.now(timezone.utc)}
    
    if update_data.name is not None:
        update_doc["name"] = update_data.name
    if update_data.phone is not None:
        update_doc["phone"] = update_data.phone
    if update_data.home_city is not None:
        update_doc["home_city"] = update_data.home_city
    if update_data.onboarding_completed is not None:
        update_doc["onboarding_completed"] = update_data.onboarding_completed
    if update_data.preferences is not None:
        update_doc["preferences"] = update_data.preferences.model_dump()
    if update_data.subscription_tier is not None:
        update_doc["subscription_tier"] = update_data.subscription_tier
    
    result = await users.find_one_and_update(
        {"firebase_id": token_data["uid"]},
        {"$set": update_doc},
        return_document=True
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    
    result["_id"] = str(result["_id"])
    return result


@router.post("/logout", response_model=dict)
async def logout(token_data: dict = Depends(verify_firebase_token)):
    """Log out user (client should revoke token)."""
    users = users_collection()
    await users.update_one(
        {"firebase_id": token_data["uid"]},
        {"$set": {"last_logout": datetime.now(timezone.utc)}}
    )
    return {"status": "logged_out"}


# === DPDP Act Compliance: Right to Erasure ===

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
    """
    user_id = token_data["uid"]
    
    # Perform cascade deletion
    stats = await UserDeletionService.delete_user_completely(user_id)
    
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
    all_clear = not any(checks.values())
    
    return {
        "user_id": user_id,
        "deletion_complete": all_clear,
        "remaining_data": checks
    }
