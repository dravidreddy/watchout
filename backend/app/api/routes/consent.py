"""
Consent API Routes for DPDP Act Compliance
"""
from fastapi import APIRouter, Depends, Request, HTTPException
from datetime import datetime

from app.core.firebase_auth import verify_firebase_token
from app.models.consent import (
    ConsentRequest, 
    ConsentWithdrawalRequest,
    ConsentResponse,
    UserConsents
)
from app.services.consent_service import ConsentService
from app.core.rate_limiter import limiter, RateLimits

router = APIRouter(prefix="/consent", tags=["Consent & Privacy"])


@router.post("/record", response_model=ConsentResponse)
@limiter.limit(RateLimits.USER_UPDATE)
async def record_consent(
    request: Request,
    consent_req: ConsentRequest,
    token_data: dict = Depends(verify_firebase_token)
):
    """
    Record user consent for data processing purposes.
    Required for DPDP Act compliance.
    
    - **purposes**: List of purposes user is consenting to
    - **agreed**: Whether user agreed to the purposes
    """
    user_id = token_data["uid"]
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Record consent for each purpose
    purposes_recorded = []
    for purpose in consent_req.purposes:
        await ConsentService.record_consent(
            user_id=user_id,
            purpose=purpose,
            consented=consent_req.agreed,
            ip_address=ip_address,
            user_agent=user_agent
        )
        purposes_recorded.append(purpose)
    
    return ConsentResponse(
        status="recorded",
        timestamp=datetime.utcnow(),
        purposes_recorded=purposes_recorded
    )


@router.get("/status", response_model=UserConsents)
@limiter.limit(RateLimits.USER_UPDATE)
async def get_consent_status(
    request: Request,
    token_data: dict = Depends(verify_firebase_token)
):
    """
    Get current consent status for the authenticated user.
    Shows which purposes the user has consented to.
    """
    user_id = token_data["uid"]
    
    consents = await ConsentService.get_all_consents(user_id)
    
    return UserConsents(
        user_id=user_id,
        consents=consents,
        last_updated=datetime.utcnow()
    )


@router.post("/withdraw")
@limiter.limit(RateLimits.USER_UPDATE)
async def withdraw_consent(
    request: Request,
    withdrawal_req: ConsentWithdrawalRequest,
    token_data: dict = Depends(verify_firebase_token)
):
    """
    Withdraw consent for a specific purpose.
    User can withdraw consent at any time as per DPDP Act.
    
    - **purpose**: The purpose to withdraw consent from
    """
    user_id = token_data["uid"]
    
    success = await ConsentService.withdraw_consent(
        user_id=user_id,
        purpose=withdrawal_req.purpose
    )
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"No active consent found for purpose: {withdrawal_req.purpose}"
        )
    
    return {
        "status": "withdrawn",
        "purpose": withdrawal_req.purpose,
        "timestamp": datetime.utcnow()
    }


@router.get("/history")
@limiter.limit(RateLimits.USER_UPDATE)
async def get_consent_history(
    request: Request,
    purpose: str = None,
    token_data: dict = Depends(verify_firebase_token)
):
    """
    Get full consent history for audit purposes.
    Optionally filter by specific purpose.
    
    - **purpose**: Optional purpose to filter history by
    """
    user_id = token_data["uid"]
    
    history = await ConsentService.get_consent_history(
        user_id=user_id,
        purpose=purpose
    )
    
    return {
        "user_id": user_id,
        "history": history,
        "count": len(history)
    }
